import os
import asyncio
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
from app.engines.news.gemini_client import check_claim_with_gemini, is_configured as gemini_configured
from app.services.evidence_evaluator import EvidenceEvaluatorService, gather_claim_evidence

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


def merge_claim_into_media(synthesis, factual_verdict, claim_text):
    """If the caption/spoken claim is contradicted by sources, say so even when the media itself looks genuine."""
    if factual_verdict in ("CONTRADICTED", "MOSTLY_CONTRADICTED") and synthesis.overall_verdict in ("AUTHENTIC", "INCONCLUSIVE", "SUSPICIOUS", "MISLEADING_CONTEXT"):
        synthesis.overall_verdict = "MISLEADING_CONTEXT"
        synthesis.verdict_label = "Claim attached to this media is contradicted by sources"
        synthesis.summary = f'The media may be genuine, but the claim made about it ("{claim_text[:140]}") is contradicted by the sources reviewed.'
        synthesis.explanation = f"**Quick Summary**: {synthesis.summary}\n\n" + synthesis.explanation.split("\n\n", 1)[-1]
    elif factual_verdict in ("SUPPORTED", "MOSTLY_SUPPORTED"):
        synthesis.explanation += f'\n\n**Caption/claim check**: sources support the claim "{claim_text[:140]}".'
    return synthesis


def _join(indicators, limit: int = 420) -> str:
    text = "; ".join(str(i) for i in indicators if i)
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def image_report_card_details(ai_res, manip_res, metadata, c2pa_res):
    """One entry per image test: risk 0-100 (None = the test could not judge) plus a plain-language reason."""
    ela = manip_res.get("ela", {})
    editing = metadata.get("editing_signatures", [])
    manip_risk = manip_res["manipulation_score"]
    if not ela.get("applicable", True) and not editing:
        manip_risk = None  # nothing was actually measured, so do not present the baseline as a result

    if c2pa_res.get("is_ai_declared"):
        prov_risk, prov_detail = 98.0, "Content Credentials in the file declare it was made by AI."
    elif metadata.get("generator_signatures"):
        prov_risk, prov_detail = 96.0, _join(metadata["generator_signatures"])
    elif c2pa_res.get("has_c2pa"):
        prov_risk, prov_detail = 8.0, "The file carries Content Credentials (C2PA) and they do not declare AI generation."
    elif metadata.get("camera_make") or metadata.get("camera_model"):
        cam = f"{metadata.get('camera_make') or ''} {metadata.get('camera_model') or ''}".strip()
        prov_risk, prov_detail = 12.0, f"The file names a physical camera ({cam}). Tags can be copied, so this lowers risk but proves nothing."
    else:
        prov_risk, prov_detail = None, "No camera data or Content Credentials in the file. Many apps strip these, so this is neutral and was not counted."

    return [
        {"key": "ai_generation", "title": "AI-generation tests", "risk": ai_res["ai_generated_score"], "detail": _join(ai_res.get("indicators", []))},
        {"key": "manipulation", "title": "Editing / pasted-region test", "risk": manip_risk,
         "detail": _join(manip_res.get("indicators", [])) or ela.get("note", "")},
        {"key": "provenance", "title": "Camera & provenance data", "risk": prov_risk, "detail": prov_detail},
    ]


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

            self.job_repo.update_progress(job_id, 35, "Asking Gemini AI and searching fact-checkers and live news")
            (scored_evidence, unavailable), gemini_res = await asyncio.gather(
                gather_claim_evidence(primary_claim),
                check_claim_with_gemini(claim_text, context),
            )
            unavailable = list(unavailable)
            ai_analysis = gemini_res if gemini_res.get("ok") else None
            if not ai_analysis:
                unavailable.append(f"Gemini AI check ({gemini_res.get('error', 'unavailable')})")
            self.job_repo.update_progress(job_id, 75, "Weighing Gemini's answer and each source by reliability")

            factual_verdict = VerdictEngine.evaluate_claim_verdict(scored_evidence)
            if ai_analysis and ai_analysis["verdict"] != "UNVERIFIABLE":
                factual_verdict = ai_analysis["factual_verdict"]

            self.job_repo.update_progress(job_id, 90, "Building the percentage evaluation table")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="claim",
                factual_verdict=factual_verdict,
                media_verdict=None,
                context_verdict=None,
                evidence_items=scored_evidence,
                detector_scores=[],
                indicators=[],
                ai_analysis=ai_analysis
            )

            if ai_analysis:
                for src in ai_analysis.get("sources", []):
                    scored_evidence.append({
                        "title": src["title"][:200], "source_name": "Google Search (via Gemini)",
                        "source_url": src["url"], "publisher": src["title"][:80],
                        "snippet": "Page Gemini consulted while checking this statement.",
                        "stance": "CONTEXT", "credibility_score": 60.0,
                    })

            limitations = [
                "Fact-checking depends on publicly indexed records and verified news databases.",
                "Emerging or hyper-local claims may have insufficient public documentation.",
                "Automated stance analysis uses lexical and semantic indicators.",
                "Gemini's percentage is an AI estimate and can be wrong, especially for very recent events."
            ]
            checks_performed = (["Google Gemini AI fact-check with percentage evaluation"] if ai_analysis else []) + [
                "Curated fact-check library match",
                "Live news search (GDELT, Google News) with article text reading",
                "Encyclopedia background references (context only, not proof)",
                "Source reliability weighting and independence check",
            ]

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Claim: {primary_claim[:60]}",
                input_type="claim",
                input_preview=claim_text,
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                correctness_score=synthesis.correctness_score,
                correctness_explanation=synthesis.correctness_explanation,
                report_card=synthesis.report_card,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=unavailable,
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

            self.job_repo.update_progress(job_id, 55, "Cross-referencing the article with fact-checkers and other news outlets")
            scored_evidence, unavailable = await gather_claim_evidence(primary_claim)
            self.job_repo.update_progress(job_id, 75, "Weighing each source by reliability and stance")
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
                "Safe retrieval and reading of the submitted article",
                "Extraction of the main checkable claim",
                "Curated fact-check library match",
                "Live news search with article text reading",
                "Source reliability weighting and independence check",
            ]

            report = self.report_repo.create_report(
                job_id=job_id,
                title=f"Article: {article['title'][:60]}",
                input_type="url",
                input_preview=f"{article['title']} — {url}",
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                correctness_score=synthesis.correctness_score,
                correctness_explanation=synthesis.correctness_explanation,
                report_card=synthesis.report_card,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=unavailable,
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
            manip_res = detect_image_manipulation(file_path, pil_img, metadata)
            similarity = find_similar_images_fingerprint(pil_img)
            context_res = evaluate_image_context(metadata, ai_res, manip_res, user_context or "")

            all_indicators = list(ai_res.get("indicators", [])) + list(manip_res.get("indicators", []))
            if metadata.get("generator_signatures"):
                all_indicators.extend(metadata["generator_signatures"])
            for sig in metadata.get("editing_signatures", []):
                if sig not in all_indicators:
                    all_indicators.append(sig)

            media_verdict = VerdictEngine.evaluate_media_authenticity(
                ai_score=ai_res["ai_generated_score"],
                manipulation_score=manip_res["manipulation_score"],
                indicators=all_indicators,
                has_c2pa=c2pa_res["has_c2pa"],
                is_c2pa_ai=c2pa_res["is_ai_declared"],
                has_provenance=bool(metadata.get("camera_make") or metadata.get("camera_model"))
            )

            caption_evidence, caption_unavailable, caption_verdict = [], [], None
            if user_context and len(user_context.strip()) >= 8:
                self.job_repo.update_progress(job_id, 82, "Checking the caption/claim against fact-checkers and live news")
                caption_evidence, caption_unavailable = await gather_claim_evidence(user_context.strip())
                caption_verdict = VerdictEngine.evaluate_claim_verdict(caption_evidence)

            self.job_repo.update_progress(job_id, 90, "Synthesizing multi-modal media verdict")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="image",
                factual_verdict=caption_verdict,
                media_verdict=media_verdict,
                context_verdict=context_res.get("context_verdict"),
                evidence_items=caption_evidence,
                detector_scores=[ai_res["ai_generated_score"], manip_res["manipulation_score"]],
                indicators=all_indicators,
                detector_details=image_report_card_details(ai_res, manip_res, metadata, c2pa_res)
            )
            if caption_verdict:
                synthesis = merge_claim_into_media(synthesis, caption_verdict, user_context.strip())

            checks_performed = [
                "File Signature & Integrity Validation",
                "EXIF Camera & Software Metadata Analysis",
                "C2PA Content Credentials & Manifest Inspection",
                "2D Fast Fourier Transform (FFT) Frequency Analysis",
                "Sensor PRNU Noise Residual Correlation",
                "Error Level Analysis (ELA) Splicing Detection",
                "Perceptual Difference & Average Hashing"
            ] + (["Caption/claim fact-check against live news and fact-checkers"] if caption_verdict else [])
            limitations = [
                "Heuristic frequency detectors can be affected by aggressive social media recompression.",
                "Absence of EXIF tags does not guarantee manipulation, as many platforms strip metadata.",
                "Detection scores represent statistical anomaly likelihood, not legal certainty.",
                "The built-in tests cannot reliably recognise modern AI images that carry no metadata or Content Credentials; a trained detection model is needed for that.",
                "Error-level analysis only applies to JPEG photos and can give false hints on freshly resized or re-saved pictures."
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
                input_preview=(f"{file_path.name}\nCaption: {user_context.strip()}" if user_context and user_context.strip() else file_path.name),
                overall_verdict=synthesis.overall_verdict,
                verdict_label=synthesis.verdict_label,
                confidence_score=synthesis.confidence_score,
                confidence_level=synthesis.confidence_level.value,
                summary=synthesis.summary,
                explanation=synthesis.explanation,
                correctness_score=synthesis.correctness_score,
                correctness_explanation=synthesis.correctness_explanation,
                report_card=synthesis.report_card,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=["Reverse image search (needs an external image-search service)"] + caption_unavailable,
                media_authenticity_verdict=media_verdict,
                context_verdict=context_res.get("context_verdict"),
                factual_claim_verdict=caption_verdict,
                evidence_items=caption_evidence,
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

            forensics_ok = bool(waveform.get("available"))
            if forensics_ok:
                self.job_repo.update_progress(job_id, 70, "Detecting synthetic speech & voice cloning signatures")
                synthetic_res = detect_synthetic_speech(waveform, meta)
                cloning_res = detect_voice_cloning_deepfake(synthetic_res, waveform)
                consistency = evaluate_speaker_consistency(waveform)
            else:
                synthetic_res = {"synthetic_voice_probability": 0.0, "is_synthetic": False, "indicators": []}
                cloning_res = {"cloning_probability": 0.0, "voice_cloning_detected": False, "indicators": []}
                consistency = {"speaker_consistency_score": 0.0, "splicing_detected": False, "note": "Not analysed"}

            self.job_repo.update_progress(job_id, 85, "Cross-checking spoken claims against factual evidence")
            claim_check = await check_speech_factual_claims(transcription.get("full_transcript", ""))
            audio_unavailable = list(claim_check.get("unavailable", []))
            if not transcription.get("full_transcript"):
                audio_unavailable.append("Speech transcription and spoken-claim check (install openai-whisper to enable)")

            all_indicators = list(cloning_res.get("indicators", []))
            if forensics_ok:
                media_verdict = VerdictEngine.evaluate_media_authenticity(
                    ai_score=cloning_res["cloning_probability"],
                    manipulation_score=40.0 if consistency["splicing_detected"] else 10.0,
                    indicators=all_indicators
                )
                audio_scores = [cloning_res["cloning_probability"]]
            else:
                media_verdict = "INCONCLUSIVE"
                audio_scores = []
                audio_unavailable.append("Voice forensics (this audio could not be decoded; install ffmpeg or upload a WAV file)")

            self.job_repo.update_progress(job_id, 95, "Synthesizing audio verdict and speech claim status")
            synthesis = VerdictEngine.synthesize_overall_verdict(
                input_type="audio",
                factual_verdict=claim_check.get("claim_verdict"),
                media_verdict=media_verdict,
                context_verdict=None,
                evidence_items=claim_check.get("evidence", []),
                detector_scores=audio_scores,
                indicators=all_indicators,
                detector_details=[
                    {"key": "synthetic_voice", "title": "Synthetic / cloned voice tests",
                     "risk": cloning_res["cloning_probability"] if forensics_ok else None,
                     "detail": _join(all_indicators) if forensics_ok else "The audio could not be decoded, so these tests did not run."},
                    {"key": "splicing", "title": "Speaker consistency / splicing",
                     "risk": (40.0 if consistency.get("splicing_detected") else 10.0) if forensics_ok else None,
                     "detail": consistency.get("note", "") if forensics_ok else "Not analysed."},
                ]
            )
            if claim_check.get("claim_verdict"):
                synthesis = merge_claim_into_media(synthesis, claim_check["claim_verdict"], claim_check.get("primary_claim", ""))

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
                correctness_score=synthesis.correctness_score,
                correctness_explanation=synthesis.correctness_explanation,
                report_card=synthesis.report_card,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=audio_unavailable,
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
                if wf.get("available"):
                    audio_analysis_res = detect_synthetic_speech(wf, {})

            lip_sync = check_lip_sync_consistency(audio_path is not None, frame_analyses)

            transcript_text, video_claim, video_evidence, video_unavailable = "", {}, [], []
            if audio_path:
                transcription = transcribe_audio_file(audio_path)
                transcript_text = transcription.get("full_transcript", "")
                if transcript_text:
                    video_claim = await check_speech_factual_claims(transcript_text)
                    video_evidence = video_claim.get("evidence", [])
                    video_unavailable = list(video_claim.get("unavailable", []))
                else:
                    video_unavailable.append("Speech transcription and spoken-claim check (install openai-whisper to enable)")
            else:
                video_unavailable.append("Audio track analysis (no audio stream or ffmpeg unavailable)")
            video_unavailable.append("Lip-sync analysis (needs a face-landmark model)")

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
                factual_verdict=video_claim.get("claim_verdict"),
                media_verdict=media_verdict,
                context_verdict=None,
                evidence_items=video_evidence,
                detector_scores=[aggregated["deepfake_score"], aggregated["temporal_score"]],
                indicators=all_indicators,
                detector_details=[
                    {"key": "frames", "title": "Frame-level AI artifact tests", "risk": aggregated["average_frame_artifact_score"],
                     "detail": f"{aggregated['total_frames_analyzed']} frame(s) sampled; peak frame score {aggregated['peak_frame_score']}/100."},
                    {"key": "temporal", "title": "Frame-to-frame consistency", "risk": aggregated["temporal_score"],
                     "detail": "Weak signal: frames are sampled seconds apart, so normal movement and cuts also cause differences. It can add to other evidence but cannot flag a video alone."},
                    {"key": "audio_voice", "title": "Audio track voice test",
                     "risk": aggregated["audio_synthetic_score"] if audio_analysis_res else None,
                     "detail": "Checked the audio track for synthetic-voice signs." if audio_analysis_res else "No usable audio track, so this test did not run."},
                ]
            )
            if video_claim.get("claim_verdict"):
                synthesis = merge_claim_into_media(synthesis, video_claim["claim_verdict"], video_claim.get("primary_claim", ""))

            checks_performed = [
                "Video Container & Stream Parameter Inspection",
                "Keyframe Extraction at Sampling Intervals",
                "Frame-Level Generative Artifact Analysis",
                "Inter-Frame Illumination & Boundary Temporal Continuity",
                "Audio Stream Extraction & Synthetic Voice Analysis",
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
                correctness_score=synthesis.correctness_score,
                correctness_explanation=synthesis.correctness_explanation,
                report_card=synthesis.report_card,
                limitations=limitations,
                checks_performed=checks_performed,
                checks_unavailable=video_unavailable,
                media_authenticity_verdict=media_verdict,
                factual_claim_verdict=video_claim.get("claim_verdict"),
                evidence_items=video_evidence,
                media_analysis_data={**media_analysis_data, "transcript": transcript_text or None}
            )

            self.job_repo.complete_job(job_id, report.id)
            return report.id
        except Exception as e:
            logger.exception(f"Video verification failed for job {job_id}: {e}")
            self.job_repo.fail_job(job_id, str(e))
            raise
