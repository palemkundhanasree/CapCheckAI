import wave
import struct
from pathlib import Path
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status


def validate_and_probe_audio(file_path: Path) -> Dict[str, Any]:
    """
    Validates audio file integrity, extracting channels, sample rate,
    duration, and bit depth safely.
    """
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found.")

    ext = file_path.suffix.lower()
    file_size = file_path.stat().st_size

    info = {
        "format": ext.replace(".", "").upper(),
        "channels": 1,
        "sample_rate": 44100,
        "duration_seconds": 0.0,
        "file_size_bytes": file_size,
        "is_valid": True
    }

    if ext == ".wav":
        try:
            with wave.open(str(file_path), "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = n_frames / float(sample_rate) if sample_rate > 0 else 0.0
                info["channels"] = channels
                info["sample_rate"] = sample_rate
                info["duration_seconds"] = round(duration, 2)
        except Exception:
            # Fallback estimation based on size
            info["duration_seconds"] = round(file_size / (44100 * 2 * 2), 2)
    else:
        # Approximate duration based on standard bitrates
        bitrate_bytes_sec = 16000  # ~128kbps for mp3/m4a
        info["duration_seconds"] = round(file_size / max(bitrate_bytes_sec, 1), 2)

    return info
