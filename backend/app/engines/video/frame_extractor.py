import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image
from app.config import settings

logger = logging.getLogger(__name__)


def extract_video_frames(
    video_path: Path,
    sample_interval_sec: float = 1.0,
    max_frames: int = 10
) -> Tuple[List[Path], Dict[str, Any]]:
    """
    Samples frames from video without loading entire video into memory.
    Uses OpenCV if available, otherwise generates structured frame representations.
    Returns (list_of_saved_frame_paths, video_meta).
    """
    frames_paths: List[Path] = []
    meta = {
        "duration_seconds": 0.0,
        "fps": 30.0,
        "total_frames": 0,
        "width": 1280,
        "height": 720,
        "method": "opencv"
    }

    opencv_available = False
    try:
        import cv2
        opencv_available = True
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0.0

            meta.update({
                "duration_seconds": round(duration, 2),
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "width": width,
                "height": height
            })

            frame_step = max(int(fps * sample_interval_sec), 1)
            frame_idx = 0
            saved_count = 0

            while cap.isOpened() and saved_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_step == 0:
                    # Save frame as JPEG
                    frame_filename = f"frame_{video_path.stem}_{saved_count:03d}.jpg"
                    frame_path = settings.TEMP_DIR / frame_filename
                    cv2.imwrite(str(frame_path), frame)
                    frames_paths.append(frame_path)
                    saved_count += 1

                frame_idx += 1

            cap.release()
    except ImportError:
        logger.info("OpenCV not installed. Using synthetic frame proxy generator.")
    except Exception as e:
        logger.warning(f"Error during OpenCV frame extraction: {e}")

    if not frames_paths:
        frames_paths = _extract_frames_with_ffmpeg(video_path, max_frames)
        if frames_paths:
            meta.update({"method": "ffmpeg", "width": None, "height": None, "fps": None})

    if not frames_paths:
        raise ValueError(
            "This video could not be analysed because no frames could be read. "
            "Install OpenCV (pip install opencv-python-headless) or ffmpeg, or try an MP4 file."
        )

    return frames_paths, meta


def _extract_frames_with_ffmpeg(video_path: Path, max_frames: int) -> List[Path]:
    """Fallback frame sampler (one frame every 2 seconds) using ffmpeg when OpenCV is unavailable."""
    import subprocess
    pattern = settings.TEMP_DIR / f"frame_{video_path.stem}_ff_%03d.jpg"
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(video_path), "-vf", "fps=0.5", "-frames:v", str(max_frames), str(pattern)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    return sorted(settings.TEMP_DIR.glob(f"frame_{video_path.stem}_ff_*.jpg"))
