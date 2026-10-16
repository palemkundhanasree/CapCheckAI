from typing import Dict, Any


def evaluate_speaker_consistency(waveform: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether the speaker acoustic profile is stable or exhibits sudden splicing cuts.
    """
    energy_var = waveform.get("energy_variance", 0.02)
    # High variance in clean speech may suggest abrupt cuts or speaker splicing
    is_spliced = energy_var > 0.08

    return {
        "speaker_consistency_score": round(max(100.0 - (energy_var * 400), 40.0), 1),
        "splicing_detected": is_spliced,
        "note": "No abrupt loudness jumps that would suggest cuts (a basic check; speaker identity is not compared)." if not is_spliced else "Potential splicing boundary detected."
    }
