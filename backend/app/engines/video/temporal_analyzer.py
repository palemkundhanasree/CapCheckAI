from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from PIL import Image


def analyze_temporal_consistency(frames: List[Path]) -> Dict[str, Any]:
    """
    Measures inter-frame jitter, unnatural illumination shifts,
    and frame-to-frame boundary flickering across adjacent frames.
    """
    if len(frames) < 2:
        return {
            "temporal_inconsistency_score": 10.0,
            "mean_interframe_delta": 0.0,
            "has_flicker_anomalies": False
        }

    deltas = []
    prev_gray = None

    for f_path in frames:
        img = Image.open(f_path).convert("L").resize((256, 144), Image.Resampling.BILINEAR)
        arr = np.array(img).astype(np.float32)
        if prev_gray is not None:
            delta = float(np.mean(np.abs(arr - prev_gray)))
            deltas.append(delta)
        prev_gray = arr

    mean_delta = float(np.mean(deltas)) if deltas else 0.0
    std_delta = float(np.std(deltas)) if deltas else 0.0

    # Unnatural temporal instability: spikes in delta between adjacent frames
    has_flicker = std_delta > 18.0
    inconsistency_score = min(max(std_delta * 3.5, 8.0), 90.0)

    return {
        "temporal_inconsistency_score": round(inconsistency_score, 1),
        "mean_interframe_delta": round(mean_delta, 2),
        "interframe_delta_variance": round(std_delta, 2),
        "has_flicker_anomalies": has_flicker
    }
