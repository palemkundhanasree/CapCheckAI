from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
from app.engines.image.ai_image_detector import detect_ai_generation
from app.engines.image.manipulation_detector import perform_error_level_analysis


def analyze_frame_deepfake(frame_path: Path, frame_idx: int, timestamp: float) -> Dict[str, Any]:
    """
    Analyzes an individual video frame for deepfake, face-swap, and generative manipulation indicators.
    """
    img = Image.open(frame_path).convert("RGB")
    ai_res = detect_ai_generation(frame_path, img)
    ela_res = perform_error_level_analysis(img)

    anomalies = []
    if ai_res["is_ai_generated"]:
        anomalies.append("Generative frequency artifacts detected on frame")
    if ela_res["splicing_detected"]:
        anomalies.append("Localized compression mismatch on frame region")

    artifact_score = round(ai_res["ai_generated_score"] * 0.7 + (35.0 if ela_res["splicing_detected"] else 0.0), 1)

    return {
        "frame_index": frame_idx,
        "timestamp_seconds": round(timestamp, 2),
        "artifact_score": min(artifact_score, 100.0),
        "anomalies": anomalies,
        "is_suspicious": artifact_score >= 55.0
    }


def analyze_sampled_frames(frames: List[Path], interval_sec: float = 1.0) -> List[Dict[str, Any]]:
    results = []
    for idx, path in enumerate(frames):
        ts = idx * interval_sec
        res = analyze_frame_deepfake(path, idx, ts)
        results.append(res)
    return results
