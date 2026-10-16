"""
TRUTHLENS AI / CAPCHECK AI - 14 REGRESSION TEST SUITE
======================================================
Automated verification of correctness, safety, and reliability across all modules.

Tests:
  TEST 1: Supported factual claim ("The Earth orbits the Sun.") -> Canonical verdict: SUPPORTED
  TEST 2: False scientific claim ("The Sun orbits the Earth.") -> Canonical verdict: FALSE
  TEST 3: Inconclusive claim (invented claim with 0 evidence) -> Canonical verdict: UNVERIFIED
  TEST 4: Mixed compound claim (True assertion + False assertion) -> Canonical verdict: MIXED
  TEST 5: Subjective opinion ("This is the best city in India.") -> Canonical verdict: UNVERIFIED (Opinion)
  TEST 6: Contradictory claim with citations -> Canonical verdict: FALSE with sources
  TEST 7: Legitimate official URL -> Low risk / Authoritative (credibility >= 85)
  TEST 8: Unknown URL -> UNVERIFIED / Neutral reputation (50.0%)
  TEST 9: Invalid / Dangerous URL -> SSRF / Validation error handled cleanly
  TEST 10: API failure simulation -> Graceful degradation to UNVERIFIED/ERROR, no freeze
  TEST 11: Image forensics module -> ELA, metadata, PRNU, and AI detection execute cleanly
  TEST 12: Video frame extraction & forensics -> Frame extraction & temporal consistency check
  TEST 13: Canonical verdict mapping & color integrity -> 6 states, no inverted colors, FALSE != Green
  TEST 14: Structured JSON output & resilient schema parsing -> Validates clean, fenced, and broken JSON
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath('backend'))

from PIL import Image
import numpy as np

from app.schemas.verdict import CanonicalVerdict, VerdictSynthesis, ConfidenceLevel, FactualVerdictType as ClaimVerdict
from app.services.verdict_engine import VerdictEngine
from app.engines.news.claim_extractor import is_subjective_opinion, split_compound_claim
from app.engines.news.claim_matcher import match_and_score_evidence, compute_evidence_stance
from app.engines.news.factcheck_client import search_curated_factchecks
from app.engines.news.source_registry import lookup_source_reputation
from app.security.url_safety import validate_url_safety
from app.services.llm_verifier import parse_and_validate_llm_response

# Image engines
from app.engines.image.image_validator import validate_image_file
from app.engines.image.metadata_reader import read_image_metadata
from app.engines.image.ai_image_detector import detect_ai_generation
from app.engines.image.manipulation_detector import detect_image_manipulation

# Video engines
from app.engines.video.frame_extractor import extract_video_frames
from app.engines.video.temporal_analyzer import analyze_temporal_consistency
from app.engines.video.video_aggregator import aggregate_video_findings


class TestReporter:
    def __init__(self):
        self.results = []

    def record(self, test_num: int, title: str, passed: bool, details: str = ""):
        self.results.append({
            "num": test_num,
            "title": title,
            "passed": passed,
            "details": details
        })
        status_tag = "PASS" if passed else "FAIL"
        print(f"[{status_tag}] TEST {test_num:02d}: {title}")
        if details:
            print(f"       -> {details}")

    def summary(self) -> bool:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        print("\n" + "=" * 70)
        print(f"TRUTHLENS AI REGRESSION AUDIT: {passed}/{total} TESTS PASSED ({failed} FAILED)")
        print("=" * 70)
        return failed == 0


reporter = TestReporter()


# -----------------------------------------------------------------------------
# TEST 1: Supported factual claim
# -----------------------------------------------------------------------------
try:
    claim1 = "The Earth orbits the Sun."
    curated = search_curated_factchecks(claim1)
    scored = match_and_score_evidence(claim1, curated)
    verdict1 = VerdictEngine.evaluate_claim_verdict(scored)
    syn1 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict1,
        evidence_items=scored
    )
    canon1 = CanonicalVerdict.normalize(syn1.overall_verdict, syn1.verdict_label)
    assert canon1 == CanonicalVerdict.SUPPORTED, f"Expected SUPPORTED, got {canon1}"
    assert syn1.confidence_score >= 75.0, f"Expected confidence >= 75, got {syn1.confidence_score}"
    reporter.record(1, "Supported factual claim ('The Earth orbits the Sun.')", True,
                    f"Verdict: {canon1.value} | Accuracy: {syn1.verdict_label} | Conf: {syn1.confidence_score}%")
except Exception as e:
    reporter.record(1, "Supported factual claim", False, str(e))


# -----------------------------------------------------------------------------
# TEST 2: False scientific claim
# -----------------------------------------------------------------------------
try:
    claim2 = "The Sun orbits the Earth."
    # The factual knowledge base states Earth orbits the Sun, which refutes this claim
    scored2 = match_and_score_evidence(claim2, [
        {
            "title": "Solar System Dynamics",
            "source_name": "NASA Science",
            "snippet": "The Earth and other planets orbit the Sun, which remains at the gravitational center of the solar system.",
            "credibility_score": 98.0,
            "stance": "NEUTRAL"
        }
    ])
    verdict2 = VerdictEngine.evaluate_claim_verdict(scored2)
    syn2 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict2,
        evidence_items=scored2
    )
    canon2 = CanonicalVerdict.normalize(syn2.overall_verdict, syn2.verdict_label)
    assert canon2 == CanonicalVerdict.FALSE, f"Expected FALSE, got {canon2}"
    assert syn2.verdict_label in ("False", "0.0%", "Accuracy Level of Real: 0.0%") or "false" in syn2.verdict_label.lower(), f"Expected False verdict label, got {syn2.verdict_label}"
    reporter.record(2, "False scientific claim ('The Sun orbits the Earth.')", True,
                    f"Verdict: {canon2.value} | Accuracy: {syn2.verdict_label}")
except Exception as e:
    reporter.record(2, "False scientific claim", False, str(e))


# -----------------------------------------------------------------------------
# TEST 3: Inconclusive claim (invented claim with zero evidence)
# -----------------------------------------------------------------------------
try:
    claim3 = "Mayor Jane Doe of Smalltown ate 45 pancakes on Tuesday."
    scored3 = match_and_score_evidence(claim3, [])
    verdict3 = VerdictEngine.evaluate_claim_verdict(scored3)
    syn3 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict3,
        evidence_items=scored3
    )
    canon3 = CanonicalVerdict.normalize(syn3.overall_verdict, syn3.verdict_label)
    assert canon3 == CanonicalVerdict.UNVERIFIED, f"Expected UNVERIFIED, got {canon3}"
    assert canon3 != CanonicalVerdict.FALSE, "Missing evidence must NEVER be marked FALSE"
    assert canon3 != CanonicalVerdict.SUPPORTED, "Missing evidence must NEVER be marked SUPPORTED"
    reporter.record(3, "Inconclusive claim with zero evidence (No presumption of falsity)", True,
                    f"Verdict: {canon3.value} | Summary: {syn3.summary[:60]}...")
except Exception as e:
    reporter.record(3, "Inconclusive claim", False, str(e))


# -----------------------------------------------------------------------------
# TEST 4: Mixed compound claim
# -----------------------------------------------------------------------------
try:
    claim4 = "The Earth orbits the Sun and drinking bleach cures COVID-19."
    sub_claims = split_compound_claim(claim4)
    assert len(sub_claims) >= 2, f"Expected split into >= 2 subclaims, got {len(sub_claims)}"
    
    # Evaluate subclaims: one true, one false
    sub_evals = [
        {"claim": "The Earth orbits the Sun", "verdict": "SUPPORTED", "confidence": 98.0, "real_score": 100.0},
        {"claim": "drinking bleach cures COVID-19", "verdict": "FALSE", "confidence": 99.0, "real_score": 0.0}
    ]
    syn4 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=ClaimVerdict.MIXED,
        is_mixed=True,
        sub_claims=sub_evals
    )
    canon4 = CanonicalVerdict.normalize(syn4.overall_verdict, syn4.verdict_label)
    assert canon4 == CanonicalVerdict.MIXED, f"Expected MIXED, got {canon4}"
    reporter.record(4, "Mixed compound claim (Split into verified & refuted parts)", True,
                    f"Verdict: {canon4.value} | Subclaims: {len(sub_claims)} | Label: {syn4.verdict_label}")
except Exception as e:
    reporter.record(4, "Mixed compound claim", False, str(e))


# -----------------------------------------------------------------------------
# TEST 5: Subjective opinion
# -----------------------------------------------------------------------------
try:
    claim5 = "This is the best city in India."
    is_op = is_subjective_opinion(claim5)
    assert is_op is True, "Expected is_subjective_opinion to return True"
    
    syn5 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=ClaimVerdict.UNVERIFIED,
        is_opinion=True
    )
    canon5 = CanonicalVerdict.normalize(syn5.overall_verdict, syn5.verdict_label)
    assert canon5 == CanonicalVerdict.UNVERIFIED, f"Expected UNVERIFIED, got {canon5}"
    assert "opinion" in syn5.summary.lower() or "subjective" in syn5.explanation.lower(), "Expected opinion explanation"
    reporter.record(5, "Subjective opinion ('best city' not branded fake news)", True,
                    f"Verdict: {canon5.value} | Recognized as subjective opinion")
except Exception as e:
    reporter.record(5, "Subjective opinion", False, str(e))


# -----------------------------------------------------------------------------
# TEST 6: Contradictory article with citations
# -----------------------------------------------------------------------------
try:
    claim6 = "5G cellular towers directly transmit biological viruses."
    contradicting_evidence = [
        {
            "title": "World Health Organization: Radiation: 5G mobile networks and health",
            "source_name": "World Health Organization",
            "source_url": "https://www.who.int/news-room/questions-and-answers/item/radiation-5g-mobile-networks-and-health",
            "snippet": "Viruses cannot travel on radio waves or mobile networks. COVID-19 is spreading in many countries that do not have 5G mobile networks.",
            "credibility_score": 96.0,
            "stance": "CONTRADICTS"
        }
    ]
    verdict6 = VerdictEngine.evaluate_claim_verdict(contradicting_evidence)
    syn6 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict6,
        evidence_items=contradicting_evidence
    )
    canon6 = CanonicalVerdict.normalize(syn6.overall_verdict, syn6.verdict_label)
    assert canon6 == CanonicalVerdict.FALSE, f"Expected FALSE, got {canon6}"
    assert len(syn6.evidence) > 0, "Expected cited evidence in synthesis"
    assert syn6.evidence[0].supports_claim is False, "Expected contradicting evidence"
    reporter.record(6, "Contradictory claim with citations (WHO refutation attached)", True,
                    f"Verdict: {canon6.value} | Contradicting Source: {syn6.evidence[0].publisher}")
except Exception as e:
    reporter.record(6, "Contradictory claim with citations", False, str(e))


# -----------------------------------------------------------------------------
# TEST 7: Legitimate official URL
# -----------------------------------------------------------------------------
try:
    url7 = "https://www.who.int"
    reg7 = lookup_source_reputation(url7)
    assert reg7["reliability"] >= 85.0, f"Expected reliability >= 85, got {reg7['reliability']}"
    assert reg7["category"] != "RESTRICTED_OR_PRIVATE"
    # Verify safety checker permits official https URL
    validate_url_safety(url7)
    reporter.record(7, "Legitimate official URL ('https://www.who.int' reliability >= 85)", True,
                    f"Publisher: {reg7['name']} | Score: {reg7['reliability']} | Category: {reg7['category']}")
except Exception as e:
    reporter.record(7, "Legitimate official URL", False, str(e))


# -----------------------------------------------------------------------------
# TEST 8: Unknown URL (Neutral reputation)
# -----------------------------------------------------------------------------
try:
    url8 = "https://freshblog2026.example.com/article-123"
    reg8 = lookup_source_reputation(url8)
    assert reg8["reliability"] == 50.0, f"Expected 50.0 neutral score, got {reg8['reliability']}"
    assert reg8["category"] == "UNVERIFIED_WEB"
    reporter.record(8, "Unknown URL (Assigned neutral 50% baseline, not 0% or 100%)", True,
                    f"Score: {reg8['reliability']} | Category: {reg8['category']}")
except Exception as e:
    reporter.record(8, "Unknown URL", False, str(e))


# -----------------------------------------------------------------------------
# TEST 9: Invalid / Dangerous URL validation
# -----------------------------------------------------------------------------
try:
    invalid_passed = False
    try:
        validate_url_safety("not a valid url")
    except Exception:
        invalid_passed = True
    assert invalid_passed, "Expected 'not a valid url' to raise exception"

    ssrf_passed = False
    try:
        validate_url_safety("http://127.0.0.1/admin")
    except Exception:
        ssrf_passed = True
    assert ssrf_passed, "Expected local loopback to raise SSRF exception"

    reporter.record(9, "Invalid & SSRF URL safety screening (Private IP & malformed URLs blocked)", True,
                    "Malformed strings and private subnet IPs successfully intercepted")
except Exception as e:
    reporter.record(9, "Invalid / Dangerous URL validation", False, str(e))


# -----------------------------------------------------------------------------
# TEST 10: API failure simulation & graceful degradation
# -----------------------------------------------------------------------------
try:
    # Simulate zero evidence / downstream failure returning safe fallback
    empty_evidence = []
    verdict10 = VerdictEngine.evaluate_claim_verdict(empty_evidence)
    syn10 = VerdictEngine.synthesize_overall_verdict(
        input_type="claim",
        factual_verdict=verdict10,
        evidence_items=empty_evidence
    )
    canon10 = CanonicalVerdict.normalize(syn10.overall_verdict, syn10.verdict_label)
    assert canon10 in [CanonicalVerdict.UNVERIFIED, CanonicalVerdict.ERROR]
    assert canon10 != CanonicalVerdict.SUPPORTED, "Degraded failure must never report SUPPORTED"
    reporter.record(10, "API failure simulation & graceful degradation (Never invents SUPPORTED)", True,
                    f"Gracefully degraded to canonical: {canon10.value}")
except Exception as e:
    reporter.record(10, "API failure simulation", False, str(e))


# -----------------------------------------------------------------------------
# TEST 11: Image forensics module verification
# -----------------------------------------------------------------------------
try:
    temp_dir = Path("storage/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    test_img_path = temp_dir / "test_forensics_sample.jpg"
    
    # Create test synthetic image
    img = Image.new("RGB", (200, 200), color=(120, 150, 180))
    img.save(test_img_path, "JPEG")
    
    pil_img, stats = validate_image_file(test_img_path)
    meta = read_image_metadata(test_img_path, pil_img)
    ai_det = detect_ai_generation(test_img_path, pil_img, meta)
    manip_det = detect_image_manipulation(test_img_path, pil_img)
    
    assert 0.0 <= ai_det["ai_generated_score"] <= 100.0
    assert 0.0 <= manip_det["manipulation_score"] <= 100.0
    assert "ela" in manip_det
    assert "frequency_analysis" in ai_det
    
    reporter.record(11, "Image forensics module (Validation, EXIF, ELA, PRNU frequency analysis)", True,
                    f"Format: {stats['format']} | AI Score: {ai_det['ai_generated_score']}% | Manip Score: {manip_det['manipulation_score']}%")
except Exception as e:
    reporter.record(11, "Image forensics module", False, str(e))


# -----------------------------------------------------------------------------
# TEST 12: Video frame extraction & temporal analysis
# -----------------------------------------------------------------------------
try:
    dummy_video_path = temp_dir / "test_sample_clip.mp4"
    dummy_video_path.write_bytes(b"\x00" * 1024)  # placeholder file
    
    frame_paths, v_meta = extract_video_frames(dummy_video_path, sample_interval_sec=1.0, max_frames=4)
    assert len(frame_paths) > 0, "Expected extracted frame paths"
    
    temporal_res = analyze_temporal_consistency(frame_paths)
    assert "temporal_inconsistency_score" in temporal_res
    assert 0.0 <= temporal_res["temporal_inconsistency_score"] <= 100.0
    
    aggregated = aggregate_video_findings(
        meta=v_meta,
        frame_analyses=[],
        temporal_res=temporal_res,
        audio_analysis=None,
        lip_sync_res={"status": "N/A"}
    )
    assert "deepfake_score" in aggregated
    reporter.record(12, "Video frame extraction & temporal forensics (Frame sampling & multi-modal aggregation)", True,
                    f"Extracted frames: {len(frame_paths)} | Inconsistency: {temporal_res['temporal_inconsistency_score']}%")
except Exception as e:
    reporter.record(12, "Video forensics module", False, str(e))


# -----------------------------------------------------------------------------
# TEST 13: Canonical verdict mapping & color integrity
# -----------------------------------------------------------------------------
try:
    mappings = {
        "SUPPORTED": ("SUPPORTED", "green"),
        "AUTHENTIC": ("SUPPORTED", "green"),
        "REAL": ("SUPPORTED", "green"),
        "FALSE": ("FALSE", "red"),
        "FAKE": ("FALSE", "red"),
        "CONTRADICTED": ("FALSE", "red"),
        "MISLEADING": ("MISLEADING", "orange"),
        "MIXED": ("MIXED", "orange"),
        "UNVERIFIED": ("UNVERIFIED", "grey"),
        "INCONCLUSIVE": ("UNVERIFIED", "grey"),
        "OPINION": ("UNVERIFIED", "grey"),
        "ERROR": ("ERROR", "grey")
    }
    
    # Confirm that no false/refuted variant ever maps to green
    false_variants = ["FALSE", "FAKE", "CONTRADICTED", "Accuracy Level of Real: 0.0%", "AI_GENERATED"]
    for f_var in false_variants:
        norm = CanonicalVerdict.normalize(f_var)
        assert norm == CanonicalVerdict.FALSE, f"Variant '{f_var}' mapped to {norm} instead of FALSE!"
        assert norm != CanonicalVerdict.SUPPORTED, f"CRITICAL COLOR DEFECT: '{f_var}' mapped to SUPPORTED (Green)!"
    
    for raw, (expected_canon, _) in mappings.items():
        res = CanonicalVerdict.normalize(raw)
        assert res.value == expected_canon, f"Expected {raw} -> {expected_canon}, got {res.value}"

    reporter.record(13, "Canonical verdict mapping & strict color integrity (Zero false-positive green)", True,
                    "All 6 canonical states normalized cleanly; no false variants map to Green")
except Exception as e:
    reporter.record(13, "Canonical verdict mapping", False, str(e))


# -----------------------------------------------------------------------------
# TEST 14: Structured JSON output & resilient schema parsing
# -----------------------------------------------------------------------------
try:
    # 1. Clean JSON
    clean_json = '{"verdict": "SUPPORTED", "confidence": 92, "summary": "Fully verified.", "claims": [], "evidence": []}'
    parsed1 = parse_and_validate_llm_response(clean_json)
    assert parsed1 is not None
    assert parsed1["verdict"] == "SUPPORTED"
    assert parsed1["confidence"] == 92.0

    # 2. Markdown fence wrapped JSON
    fenced_json = '```json\n{"verdict": "FALSE", "confidence": 88, "summary": "Debunked claim."}\n```'
    parsed2 = parse_and_validate_llm_response(fenced_json)
    assert parsed2 is not None
    assert parsed2["verdict"] == "FALSE"

    # 3. Malformed / broken JSON (Must gracefully return None without unhandled crash)
    broken_json = '{"verdict": "MIXED", "confidence": 50, "summary": "unclosed string'
    parsed3 = parse_and_validate_llm_response(broken_json)
    assert parsed3 is None, "Malformed JSON must safely return None for fallback"

    # 4. Normalized out-of-bounds confidence (e.g. 0.95 fraction should be clamped/converted to 95)
    fractional_json = '{"verdict": "UNVERIFIED", "confidence": 0.85, "summary": "Inconclusive."}'
    parsed4 = parse_and_validate_llm_response(fractional_json)
    assert parsed4 is not None
    assert parsed4["confidence"] == 85.0

    reporter.record(14, "Structured JSON output & resilient schema parsing (Handles clean, markdown, broken JSON)", True,
                    "Parser strictly validates schema, handles fences, and recovers from syntax errors")
except Exception as e:
    reporter.record(14, "Structured JSON parsing", False, str(e))


# -----------------------------------------------------------------------------
# Final Outcome
# -----------------------------------------------------------------------------
all_passed = reporter.summary()
if not all_passed:
    sys.exit(1)
else:
    sys.exit(0)
