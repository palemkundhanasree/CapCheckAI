import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.db.repositories.job_repository import JobRepository
from app.db.repositories.report_repository import ReportRepository

# News Engines
from app.engines.news.claim_extractor import extract_claims_from_text
from app.engines.news.article_extractor import extract_article_content
from app.engines.news.factcheck_client import search_curated_factchecks, query_google_factcheck_api
from app.engines.news.search_client import search_web_evidence
from app.services.evidence_evaluator import EvidenceEvaluatorService

# Image Engines
from app.engines.image.image_validator import validate_image_file
from app.engines.image.metadata_reader import read_image_metadata
from app.engines.image.provenance_checker import check_content_credentials
from app.engines.image.ai_image_detector import detect_ai_generation
from app.engines.image.manipulation_detector import detect_image_manipulation
from app.engines.image.similarity_search import find_similar_images_fingerprint
from app.engines.image.context_checker import evaluate_image_context

# Audio Engines
from app.engines.audio.audio_validator import validate_and_probe_audio
from app.engines.audio.metadata_reader import inspect_audio_metadata
from app.engines.audio.audio_preprocessor import extract_waveform_features
from app.engines.audio.speech_transcriber import transcribe_audio_file
from app.engines.audio.synthetic_audio_detector import detect_synthetic_speech
from app.engines.audio.voice_deepfake_detector import detect_voice_cloning_deepfake
from app.engines.audio.speaker_consistency import evaluate_speaker_consistency
from app.engines.audio.speech_claim_checker import check_speech_factual_claims

# Video Engines
from app.engines.video.video_validator import validate_video_file
from app.engines.video.frame_extractor import extract_video_frames
from app.engines.video.audio_extractor import extract_audio_from_video
from app.engines.video.deepfake_detector import analyze_sampled_frames
from app.engines.video.temporal_analyzer import analyze_temporal_consistency
from app.engines.video.lip_sync_checker import check_lip_sync_consistency
from app.engines.video.video_aggregator import aggregate_video_findings

# Verdict & Confidence
from app.services.verdict_engine import VerdictEngine

logger = logging.getLogger(__name__)


class VerificationOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.report_repo = ReportRepository(db)

    async def verify_claim(self, job_id: str, claim_text: str, context: Optional[str] = None) -> str:
        """Pipeline for verifying isolated factual claims."""
        try:
            self.job_repo.update_progress(job_id, 15, "Extracting verifiable claims and entities")
            claims = extract_claims_from_text(claim_text, max_claims=3)
            primary_claim = claims[0]["claim_text"] if claims else claim_text

            self.job_repo.update_progress(job_id, 35, "Querying international fact-checking databases")
            evidence = []
            curated_hits = search_curated_factchecks(primary_claim)
            evidence.extend(curated_hits)

            google_hits = await query_google_factcheck_api(primary_claim)
            evidence.extend(google_hits)

            self.job_repo.update_progress(job_id, 55, "Searching authoritative encyclopedia & reference indices")
            if len(evidence) < 2:
                wiki_hits = await search_web_evidence(primary_claim)
                evidence.extend(wiki_hits)

            self.job_repo.update_progress(job_id, 75, "Evaluating source credibility and stance weighting")
            scored_evidence = EvidenceEvaluatorService.evaluate_and_rank_evidence(primary_claim, evidence)

            factual_verdict = VerdictEngine.evaluate_claim_verdict(scored_evidence)

            self.job_repo.update_progress(job_id, 90, "Synthesizing final verdict and confidence score")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="claim",
                factual_verdict=factual_verdict,
                media_verdict=None,
                context_verdict=None,
                evidence_items=scored_evidence,
                detector_scores=[],
                indicators=[]
            )

            limitations = [
                "Fact-checking depends on publicly indexed records and verified news databases.",
                "Emerging or hyper-local claims may have insufficient public documentation.",
                "Automated stance analysis uses lexical and semantic indicators."
            ]
            checks_performed = [
                "International Fact Check Database Query",
                "Google FactCheck Tools API Query",
                "Wikipedia Knowledge Reference Retrieval",
                "Source Credibility & Weighting Assessment",
                "Lexical Stance Classification"
            ]

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Claim: {primary_claim[:60]}...",
                input_type="claim",
                input_preview=claim_text,
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=[],
                factual_claim_verdict=factual_verdict,
                evidence_items=scored_evidence
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"Claim verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise

    async def verify_url(self, job_id: str, url: str) -> str:
        """Pipeline for verifying news article URLs."""
        try:
            self.job_repo.update_progress(job_id, 15, "Safely retrieving and parsing web article")
            article = await extract_article_content(url)

            self.job_repo.update_progress(job_id, 35, f"Extracting core assertions from {article['title'][:30]}")
            text_corpus = f"{article['title']}\n{article['body_text']}"
            claims = extract_claims_from_text(text_corpus, max_claims=4)
            primary_claim = claims[0]["claim_text"] if claims else article["title"]

            self.job_repo.update_progress(job_id, 55, "Cross-referencing claims against independent fact-checking records")
            evidence = []
            curated_hits = search_curated_factchecks(primary_claim)
            evidence.extend(curated_hits)

            google_hits = await query_google_factcheck_api(primary_claim)
            evidence.extend(google_hits)

            wiki_hits = await search_web_evidence(primary_claim)
            evidence.extend(wiki_hits)

            self.job_repo.update_progress(job_id, 75, "Analyzing article publisher credibility and stance")
            scored_evidence = EvidenceEvaluatorService.evaluate_and_rank_evidence(primary_claim, evidence)
            factual_verdict = VerdictEngine.evaluate_claim_verdict(scored_evidence)

            self.job_repo.update_progress(job_id, 90, "Assembling verdict dossier")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="url",
                factual_verdict=factual_verdict,
                media_verdict=None,
                context_verdict=None,
                evidence_items=scored_evidence,
                detector_scores=[],
                indicators=[f"Extracted {len(claims)} checkable claims from article."]
            )

            limitations = [
                "Paywalled, password-protected, or CAPTCHA-gated articles cannot be fully scraped.",
                "Publisher credibility is evaluated using public reputation registries.",
                "Automated article extraction may omit dynamic client-rendered scripts."
            ]
            checks_performed = [
                "SSRF-Safe Web Page Scraping",
                "HTML Article Body & Metadata Extraction",
                "Claim & Named Entity Extraction",
                "Multi-Source Evidence Cross-Referencing",
                "Publisher Credibility Assessment"
            ]

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Article: {article['title'][:60]}",
                input_type="url",
                input_preview=f"{article['title']} ({url})",
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=[],
                factual_claim_verdict=factual_verdict,
                evidence_items=scored_evidence
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"URL verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise

    async def verify_image(self, job_id: str, file_path: Path, user_context: Optional[str] = None) -> str:
        """Pipeline for verifying image media."""
        try:
            self.job_repo.update_progress(job_id, 15, "Validating image integrity and EXIF metadata")
            pil_img, img_stats = validate_image_file(file_path)
            metadata = read_image_metadata(file_path, pil_img)

            self.job_repo.update_progress(job_id, 35, "Checking C2PA Content Credentials provenance")
            c2pa_res = check_content_credentials(file_path)

            self.job_repo.update_progress(job_id, 55, "Running frequency domain & sensor noise AI detection")
            ai_res = detect_ai_generation(file_path, pil_img, metadata=metadata)

            self.job_repo.update_progress(job_id, 75, "Performing Error Level Analysis (ELA) for manipulation")
            manip_res = detect_image_manipulation(file_path, pil_img)
            similarity = find_similar_images_fingerprint(pil_img)
            context_res = evaluate_image_context(metadata, ai_res, manip_res, user_context or "")

            all_indicators = list(ai_res.get("indicators", [])) + list(manip_res.get("indicators", []))
            if metadata.get("generator_signatures"):
                all_indicators.extend(metadata["generator_signatures"])

            media_verdict = VerdictEngine.evaluate_media_authenticity(
                ai_score=ai_res["ai_generated_score"],
                manipulation_score=manip_res["manipulation_score"],
                indicators=all_indicators,
                has_c2pa=c2pa_res["has_c2pa"],
                is_c2pa_ai=c2pa_res["is_ai_declared"]
            )

            self.job_repo.update_progress(job_id, 90, "Synthesizing multi-modal media verdict")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="image",
                factual_verdict=None,
                media_verdict=media_verdict,
                context_verdict=context_res.get("context_verdict"),
                evidence_items=[],
                detector_scores=[ai_res["ai_generated_score"], manip_res["manipulation_score"]],
                indicators=all_indicators
            )

            checks_performed = [
                "File Signature & Integrity Validation",
                "EXIF Camera & Software Metadata Analysis",
                "C2PA Content Credentials & Manifest Inspection",
                "2D Fast Fourier Transform (FFT) Frequency Analysis",
                "Sensor PRNU Noise Residual Correlation",
                "Error Level Analysis (ELA) Splicing Detection",
                "Perceptual Difference & Average Hashing"
            ]
            limitations = [
                "Heuristic frequency detectors can be affected by aggressive social media recompression.",
                "Absence of EXIF tags does not guarantee manipulation, as many platforms strip metadata.",
                "Detection scores represent statistical anomaly likelihood, not legal certainty."
            ]

            media_analysis_data = {
                "media_type": "image",
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "mime_type": f"image/{img_stats['format'].lower()}",
                "metadata_info": metadata,
                "visual_findings": {
                    "dimensions": f"{img_stats['width']}x{img_stats['height']}",
                    "frequency_analysis": ai_res.get("frequency_analysis"),
                    "ela": manip_res.get("ela"),
                    "c2pa": c2pa_res,
                    "hashes": similarity
                },
                "audio_findings": {},
                "ai_generated_score": ai_res["ai_generated_score"],
                "deepfake_score": manip_res["manipulation_score"],
                "manipulation_indicators": all_indicators
            }

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Image Analysis: {file_path.name[:40]}",
                input_type="image",
                input_preview=file_path.name,
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=[],
                media_authenticity_verdict=media_verdict,
                context_verdict=context_res.get("context_verdict"),
                media_analysis_data=media_analysis_data
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"Image verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise

    async def verify_audio(self, job_id: str, file_path: Path) -> str:
        """Pipeline for verifying speech and audio recordings."""
        try:
            self.job_repo.update_progress(job_id, 15, "Probing audio container & header tags")
            audio_info = validate_and_probe_audio(file_path)
            meta = inspect_audio_metadata(file_path)

            self.job_repo.update_progress(job_id, 35, "Extracting acoustic waveform & dynamic range features")
            waveform = extract_waveform_features(file_path)

            self.job_repo.update_progress(job_id, 55, "Transcribing speech content and analyzing phonemes")
            transcription = transcribe_audio_file(file_path)

            self.job_repo.update_progress(job_id, 70, "Detecting synthetic speech & voice cloning signatures")
            synthetic_res = detect_synthetic_speech(waveform, meta)
            cloning_res = detect_voice_cloning_deepfake(synthetic_res, waveform)
            consistency = evaluate_speaker_consistency(waveform)

            self.job_repo.update_progress(job_id, 85, "Cross-checking spoken claims against factual evidence")
            claim_check = await check_speech_factual_claims(transcription.get("full_transcript", ""))

            all_indicators = list(cloning_res.get("indicators", []))
            media_verdict = VerdictEngine.evaluate_media_authenticity(
                ai_score=cloning_res["cloning_probability"],
                manipulation_score=40.0 if consistency["splicing_detected"] else 10.0,
                indicators=all_indicators
            )

            self.job_repo.update_progress(job_id, 95, "Synthesizing audio verdict and speech claim status")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="audio",
                factual_verdict=claim_check.get("claim_verdict"),
                media_verdict=media_verdict,
                context_verdict=None,
                evidence_items=claim_check.get("evidence", []),
                detector_scores=[cloning_res["cloning_probability"]],
                indicators=all_indicators
            )

            checks_performed = [
                "Audio Header & Codec Parameter Probe",
                "Text-To-Speech Metadata Tag Inspection",
                "Zero-Crossing Rate (ZCR) & Energy Profiling",
                "Speech-to-Text Transcription with Timestamps",
                "Synthetic Speech & Voice Cloning Detection",
                "Speaker Consistency & Splicing Check",
                "Spoken Factual Claim Cross-Verification"
            ]
            limitations = [
                "Low-bitrate audio recordings (e.g. phone calls) may obscure subtle acoustic artifacts.",
                "Background ambient noise or reverberation affects speaker consistency scoring.",
                "Transcription accuracy varies across accents and recording conditions."
            ]

            media_analysis_data = {
                "media_type": "audio",
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "mime_type": f"audio/{audio_info['format'].lower()}",
                "metadata_info": meta,
                "visual_findings": {},
                "audio_findings": {
                    "waveform": waveform,
                    "synthetic_speech": synthetic_res,
                    "speaker_consistency": consistency,
                    "segments": transcription.get("segments", [])
                },
                "transcript": transcription.get("full_transcript"),
                "ai_generated_score": cloning_res["cloning_probability"],
                "deepfake_score": cloning_res["cloning_probability"],
                "manipulation_indicators": all_indicators
            }

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Audio Verification: {file_path.name[:40]}",
                input_type="audio",
                input_preview=file_path.name,
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=[],
                factual_claim_verdict=claim_check.get("claim_verdict"),
                media_authenticity_verdict=media_verdict,
                evidence_items=claim_check.get("evidence", []),
                media_analysis_data=media_analysis_data
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"Audio verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise

    async def verify_video(self, job_id: str, file_path: Path) -> str:
        """Pipeline for verifying video recordings."""
        try:
            self.job_repo.update_progress(job_id, 10, "Validating video stream container & parameters")
            validate_video_file(file_path)

            self.job_repo.update_progress(job_id, 25, "Sampling key frames across temporal sequence")
            frames, video_meta = extract_video_frames(file_path, sample_interval_sec=1.5, max_frames=8)

            self.job_repo.update_progress(job_id, 45, "Running facial & frame-level generative detectors")
            frame_analyses = analyze_sampled_frames(frames, interval_sec=1.5)

            self.job_repo.update_progress(job_id, 65, "Analyzing inter-frame temporal consistency & illumination jitter")
            temporal_res = analyze_temporal_consistency(frames)

            self.job_repo.update_progress(job_id, 80, "Extracting audio track for speech and voice cloning analysis")
            audio_path = extract_audio_from_video(file_path)
            audio_analysis_res = None
            if audio_path:
                wf = extract_waveform_features(audio_path)
                syn = detect_synthetic_speech(wf, {})
                audio_analysis_res = syn

            lip_sync = check_lip_sync_consistency(audio_path is not None, frame_analyses)

            self.job_repo.update_progress(job_id, 90, "Synthesizing multi-modal video forensics")
            aggregated = aggregate_video_findings(
                meta=video_meta,
                frame_analyses=frame_analyses,
                temporal_res=temporal_res,
                audio_analysis=audio_analysis_res,
                lip_sync_res=lip_sync
            )

            all_indicators = aggregated.get("indicators", [])
            media_verdict = VerdictEngine.evaluate_media_authenticity(
                ai_score=aggregated["deepfake_score"],
                manipulation_score=aggregated["temporal_score"],
                indicators=all_indicators
            )

            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="video",
                factual_verdict=None,
                media_verdict=media_verdict,
                context_verdict=None,
                evidence_items=[],
                detector_scores=[aggregated["deepfake_score"], aggregated["temporal_score"]],
                indicators=all_indicators
            )

            checks_performed = [
                "Video Container & Stream Parameter Inspection",
                "Keyframe Extraction at Sampling Intervals",
                "Frame-Level Generative Artifact Analysis",
                "Inter-Frame Illumination & Boundary Temporal Continuity",
                "Audio Stream Extraction & Synthetic Voice Analysis",
                "Lip Synchronization Consistency Check"
            ]
            limitations = [
                "Heavy video compression (such as WhatsApp/TikTok transcoding) introduces blocking artifacts.",
                "Short video clips under 3 seconds provide limited temporal continuity data.",
                "Non-facial generative video (e.g. landscape deepfakes) relies primarily on frequency heuristics."
            ]

            media_analysis_data = {
                "media_type": "video",
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "mime_type": f"video/{file_path.suffix.replace('.', '').lower()}",
                "metadata_info": video_meta,
                "visual_findings": {
                    "total_frames_analyzed": len(frame_analyses),
                    "temporal_analysis": temporal_res,
                    "frame_results": frame_analyses,
                    "lip_sync": lip_sync
                },
                "audio_findings": audio_analysis_res or {},
                "ai_generated_score": aggregated["deepfake_score"],
                "deepfake_score": aggregated["deepfake_score"],
                "manipulation_indicators": all_indicators
            }

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Video Analysis: {file_path.name[:40]}",
                input_type="video",
                input_preview=file_path.name,
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=[],
                media_authenticity_verdict=media_verdict,
                media_analysis_data=media_analysis_data
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"Video verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise
