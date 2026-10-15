from typing import Dict, Any, List


def detect_voice_cloning_deepfake(synthetic_res: Dict[str, Any], waveform: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assesses voice cloning indicators and spectral anomalies.
    """
    indicators = list(synthetic_res.get("indicators", []))
    cloning_prob = synthetic_res.get("synthetic_voice_probability", 10.0)

    zcr = waveform.get("zero_crossing_rate", 0.05)
    if zcr > 0.15:
        indicators.append("High-frequency whispering or phase dispersion typical of neural voice conversion models")
        cloning_prob = min(cloning_prob + 15.0, 95.0)

    return {
        "voice_cloning_detected": cloning_prob >= 55.0,
        "cloning_probability": round(cloning_prob, 1),
        "indicators": indicators
    }
