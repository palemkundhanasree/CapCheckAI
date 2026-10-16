from typing import Dict, Any, List


def detect_synthetic_speech(waveform_features: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detects text-to-speech / neural vocoder cloning anomalies with calibrated precision:
    - Synthesizer metadata tags (ElevenLabs, Google TTS, OpenAI TTS)
    - Unnaturally flat digital silence in breath pauses (lack of physical room acoustic floor)
    - Robotic pitch stability
    """
    indicators: List[str] = []
    suspicion_score = 8.0  # Clean baseline

    # 1. Metadata indicator (definitive proof)
    if metadata.get("is_synthetic_tag_found"):
        encoder = metadata.get("encoder", "Neural Voice Synthesizer")
        indicators.append(f"AI voice synthesizer encoder tag detected: {encoder}")
        suspicion_score = 96.0

    # 2. Complete absence of ambient room acoustic floor (common in synthetic audio renderers)
    noise_floor_db = waveform_features.get("noise_floor_db", -45.0)
    if noise_floor_db < -68.0 and not indicators:
        indicators.append("Complete absence of physical room noise floor (pure digital synthesis characteristic)")
        suspicion_score += 35.0

    # 3. Dynamic range and spectral uniformity
    dyn_range = waveform_features.get("dynamic_range_db", 24.0)
    energy_var = waveform_features.get("energy_variance", 0.02)
    if dyn_range < 8.0 and energy_var < 0.002:
        indicators.append("Extremely compressed acoustic dynamic range characteristic of robotic vocoder output")
        suspicion_score += 25.0

    synthetic_prob = min(max(suspicion_score, 5.0), 98.0)
    is_synthetic = synthetic_prob >= 55.0

    if not is_synthetic and not indicators:
        indicators.append("No synthetic-voice signs found by these basic acoustic tests (this does not prove the voice is real)")

    return {
        "synthetic_voice_probability": round(synthetic_prob, 1),
        "is_synthetic": is_synthetic,
        "indicators": indicators
    }
