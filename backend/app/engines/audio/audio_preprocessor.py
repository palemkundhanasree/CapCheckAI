import logging
import subprocess
import wave
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


def _load_samples(file_path: Path) -> Optional[np.ndarray]:
    """Decodes audio to mono float samples. WAV is read directly; other formats need ffmpeg."""
    def read_wav(path: Path) -> Optional[np.ndarray]:
        try:
            with wave.open(str(path), "rb") as w:
                n_ch, width, frames = w.getnchannels(), w.getsampwidth(), w.readframes(w.getnframes())
            dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(width)
            if dtype is None:
                return None
            data = np.frombuffer(frames, dtype=dtype).astype(np.float32)
            if width == 1:
                data -= 128.0
            if n_ch > 1:
                data = data[: len(data) // n_ch * n_ch].reshape(-1, n_ch).mean(axis=1)
            return data
        except Exception:
            return None

    samples = read_wav(file_path) if file_path.suffix.lower() == ".wav" else None
    if samples is not None and len(samples):
        return samples

    out = settings.TEMP_DIR / f"decoded_{file_path.stem}.wav"
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", str(file_path), "-vn", "-ac", "1", "-ar", "16000",
                            "-acodec", "pcm_s16le", str(out)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if r.returncode == 0 and out.exists():
            samples = read_wav(out)
            out.unlink(missing_ok=True)
            return samples
    except (FileNotFoundError, subprocess.SubprocessError):
        logger.info("ffmpeg not available to decode %s", file_path.name)
    return None


def extract_waveform_features(file_path: Path) -> Dict[str, Any]:
    """
    Real acoustic features measured from decoded samples: zero-crossing rate, energy statistics,
    noise floor and dynamic range (from 20 ms frame loudness). Returns {"available": False} when the
    file cannot be decoded, so no analysis is invented.
    """
    samples = _load_samples(file_path)
    if samples is None or len(samples) < 4000:
        return {"available": False}

    peak = float(np.max(np.abs(samples)))
    if peak <= 0:
        return {"available": False}
    x = samples / peak

    zcr = float(np.mean(np.abs(np.diff(np.sign(x))) > 0))
    energy = x ** 2

    frame = 320  # 20 ms at 16 kHz (approximate for other rates)
    n = len(x) // frame
    rms = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1)) if n else np.array([float(np.sqrt(np.mean(energy)))])
    rms_db = 20 * np.log10(np.maximum(rms, 1e-6))
    noise_floor_db = float(np.percentile(rms_db, 10))
    dynamic_range_db = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 10))

    return {
        "available": True,
        "zero_crossing_rate": round(zcr, 4),
        "mean_energy": round(float(np.mean(energy)), 4),
        "energy_variance": round(float(np.var(energy)), 4),
        "noise_floor_db": round(noise_floor_db, 2),
        "dynamic_range_db": round(dynamic_range_db, 2),
        "total_samples": int(len(x)),
    }
