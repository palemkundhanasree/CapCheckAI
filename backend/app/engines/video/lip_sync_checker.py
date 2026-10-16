from typing import Dict, Any, Optional


def check_lip_sync_consistency(has_audio: bool, frame_results: list) -> Dict[str, Any]:
    """
    Checks for phoneme-viseme correlation between audio and facial movements.
    """
    if not has_audio:
        return {
            "lip_sync_status": "SKIPPED_NO_AUDIO",
            "is_desynchronized": False,
            "confidence": 0.0
        }

    # Real lip-sync analysis needs face landmarks and speech alignment models that are not installed.
    # It is reported as not performed rather than guessed.
    return {
        "lip_sync_status": "NOT_PERFORMED",
        "is_desynchronized": False,
        "confidence": 0.0,
        "note": "Lip-sync analysis needs a face-landmark model and was not performed."
    }
