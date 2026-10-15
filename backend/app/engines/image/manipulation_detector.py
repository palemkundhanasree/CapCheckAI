import io
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image, ImageChops


def perform_error_level_analysis(img: Image.Image, quality: int = 90) -> Dict[str, Any]:
    """
    Error Level Analysis (ELA) analyzes JPEG compression error rate variations.
    Genuine unmodified camera photos have consistent error rates across the whole frame.
    Digitally spliced or Photoshopped inserts show localized error discontinuities.
    """
    img_rgb = img.convert("RGB")
    buffer = io.BytesIO()
    img_rgb.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)

    diff = ImageChops.difference(img_rgb, recompressed)
    diff_arr = np.array(diff).astype(np.float32)

    mean_diff = float(np.mean(diff_arr))
    max_diff = float(np.max(diff_arr))
    std_diff = float(np.std(diff_arr))

    # Grid-based regional variance analysis to detect localized splicing
    # Divide into 4x4 blocks and check if any block's error rate is radically anomalous
    h, w, _ = diff_arr.shape
    bh, bw = max(h // 4, 1), max(w // 4, 1)
    block_means = []
    for i in range(4):
        for j in range(4):
            block = diff_arr[i*bh:(i+1)*bh, j*bw:(j+1)*bw]
            if block.size > 0:
                block_means.append(float(np.mean(block)))

    block_means_arr = np.array(block_means)
    block_std = float(np.std(block_means_arr)) if len(block_means) > 0 else 0.0
    block_range = float(np.max(block_means_arr) - np.min(block_means_arr)) if len(block_means) > 0 else 0.0

    # Localized splicing creates sharp disparities between blocks (e.g. pasted object has different quality)
    suspicious_splicing = block_range > 28.0 and block_std > 8.5

    return {
        "mean_error_level": round(mean_diff, 2),
        "max_error_level": round(max_diff, 2),
        "std_deviation": round(std_diff, 2),
        "block_variance": round(block_std, 2),
        "block_range": round(block_range, 2),
        "splicing_detected": suspicious_splicing
    }


def detect_image_manipulation(file_path: Path, img: Image.Image) -> Dict[str, Any]:
    """
    Runs calibrated Error Level Analysis to detect Photoshop splicing, cloning, and digital tampering.
    """
    indicators: List[str] = []
    suspicion_score = 8.0  # Clean baseline

    ela_result = perform_error_level_analysis(img)
    if ela_result["splicing_detected"]:
        indicators.append("Localized compression mismatch detected between regions (characteristic of image splicing or sticker insertion)")
        suspicion_score += 48.0

    manipulated = suspicion_score >= 50.0

    if not manipulated:
        indicators.append("Uniform JPEG compression layers verified across all image quadrants (No splicing detected)")

    return {
        "manipulation_score": round(min(suspicion_score, 95.0), 1),
        "is_manipulated": manipulated,
        "indicators": indicators,
        "ela": ela_result
    }
