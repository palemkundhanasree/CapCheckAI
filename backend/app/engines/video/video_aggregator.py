from typing import Dict, Any, List, Optional


def aggregate_video_findings(
    meta: Dict[str, Any],
    frame_analyses: List[Dict[str, Any]],
    temporal_res: Dict[str, Any],
    audio_analysis: Optional[Dict[str, Any]] = None,
    lip_sync_res: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Synthesizes frame-level forensics, temporal jitter, and acoustic analysis into
    overall video authenticity findings.
    """
    indicators: List[str] = []

    # Frame scores
    frame_scores = [f["artifact_score"] for f in frame_analyses] if frame_analyses else [0.0]
    avg_frame_score = sum(frame_scores) / max(len(frame_scores), 1)
    max_frame_score = max(frame_scores) if frame_scores else 0.0

    temporal_score = temporal_res.get("temporal_inconsistency_score", 10.0)
    if temporal_res.get("has_flicker_anomalies"):
        indicators.append("Inter-frame temporal flickering and boundary warping observed")

    # Audio synthesis integration
    audio_score = 0.0
    if audio_analysis and audio_analysis.get("synthetic_voice_probability"):
        audio_score = audio_analysis["synthetic_voice_probability"]
        if audio_analysis.get("is_synthetic"):
            indicators.append("Audio track contains synthetic speech / cloned vocal characteristics")

    # Weighted composite deepfake score
    weights = [0.45, 0.25, 0.30] if audio_analysis else [0.65, 0.35, 0.0]
    composite_score = (
        (avg_frame_score * weights[0]) +
        (temporal_score * weights[1]) +
        (audio_score * weights[2])
    )

    is_deepfake = composite_score >= 50.0

    if max_frame_score > 60.0:
        indicators.append(f"High generative artifact concentration on {sum(1 for s in frame_scores if s > 50)} sampled keyframes")

    return {
        "deepfake_score": round(composite_score, 1),
        "is_deepfake": is_deepfake,
        "average_frame_artifact_score": round(avg_frame_score, 1),
        "peak_frame_score": round(max_frame_score, 1),
        "temporal_score": temporal_score,
        "audio_synthetic_score": round(audio_score, 1),
        "indicators": indicators,
        "total_frames_analyzed": len(frame_analyses)
    }
