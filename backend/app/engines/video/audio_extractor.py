import logging
import subprocess
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: Path) -> Optional[Path]:
    """
    Extracts audio track as WAV file from video using ffmpeg if available.
    Returns the path to extracted WAV file, or None if no audio or ffmpeg not present.
    """
    output_audio_path = settings.TEMP_DIR / f"audio_{video_path.stem}.wav"

    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(output_audio_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if result.returncode == 0 and output_audio_path.exists() and output_audio_path.stat().st_size > 100:
            return output_audio_path
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.info("ffmpeg executable not found in PATH for audio stream extraction.")
    except Exception as e:
        logger.warning(f"Audio extraction from video failed: {e}")

    return None
