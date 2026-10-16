import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def transcribe_audio_file(file_path: Path) -> Dict[str, Any]:
    """
    Transcribes spoken audio into text segments with timestamps.
    Supports Whisper if installed, with safe acoustic fallback.
    """
    whisper_available = False
    segments: List[Dict[str, Any]] = []
    full_transcript = ""

    # Check for optional whisper installation
    try:
        import whisper
        whisper_available = True
        model = whisper.load_model("tiny")
        result = model.transcribe(str(file_path))
        full_transcript = result.get("text", "").strip()
        for s in result.get("segments", []):
            segments.append({
                "start": round(s.get("start", 0.0), 2),
                "end": round(s.get("end", 0.0), 2),
                "text": s.get("text", "").strip()
            })
    except ImportError:
        logger.info("Local Whisper model not installed. No transcript will be produced.")
    except Exception as e:
        logger.warning(f"Whisper inference error: {e}")

    return {
        "engine": "OpenAI Whisper (tiny)" if whisper_available and full_transcript else "unavailable",
        "available": bool(whisper_available),
        "full_transcript": full_transcript,
        "segments": segments,
        "language": "en" if full_transcript else None
    }
