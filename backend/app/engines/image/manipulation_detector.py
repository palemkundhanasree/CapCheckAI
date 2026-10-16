import io
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image, ImageChops

# A block must change by at least this much (0-255 scale) on re-saving to count. Chosen from tests on clean and
# edited sample images: lower values flag ordinary freshly-resized photos, higher values miss most real edits.
ABS_FLOOR = 1.0
GRID = 16  # the picture is cut into GRID x GRID blocks and each block is compared with the others

# Standard JPEG luminance quantization table (libjpeg, quality 50). Used to work out the quality a file was saved at.
_STD_LUMA = np.array([
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
], dtype=np.float32)


def estimate_jpeg_quality(img: Image.Image) -> Optional[int]:
    """Returns the libjpeg quality (1-100) a JPEG was saved at, or None if it is not a JPEG / has no tables."""
    tables = getattr(img, "quantization", None)
    if not tables or 0 not in tables or len(tables[0]) != 64:
        return None
    actual = np.array(tables[0], dtype=np.float32)
    # PIL returns the table in zig-zag order, so compare the sorted values (order-independent and robust).
    actual_sorted = np.sort(actual)
    best_q, best_err = None, 1e9
    for q in range(1, 101):
        scale = 5000.0 / q if q < 50 else 200.0 - 2.0 * q
        table = np.clip(np.floor((_STD_LUMA * scale + 50.0) / 100.0), 1, 255)
        err = float(np.abs(np.sort(table) - actual_sorted).sum())
        if err < best_err:
            best_q, best_err = q, err
    return best_q


def _robust_z(values: np.ndarray, floor: float) -> np.ndarray:
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    return (values - med) / (1.4826 * mad + floor)


def perform_error_level_analysis(img: Image.Image, quality: Optional[int] = None) -> Dict[str, Any]:
    """
    Error Level Analysis (ELA) for JPEG files.

    A JPEG that was saved once changes almost nothing when it is saved again at the SAME quality. A region that
    was pasted in from another file, or edited and re-saved on its own, has a different compression history, so
    it changes noticeably more than its surroundings. To make that visible the picture is re-saved at the quality
    it was originally saved at (read from the file itself), and each block's change is compared with all other
    blocks. Only a few isolated blocks standing far out from the rest is treated as suspicious.

    ELA is meaningless for PNG/WebP/other formats (they have no JPEG history), so it reports itself as not
    applicable instead of guessing.
    """
    original_q = estimate_jpeg_quality(img) if (img.format or "").upper() in ("JPEG", "MPO") else None
    if original_q is None and quality is None:
        return {"applicable": False, "splicing_detected": False, "outlier_blocks": 0, "max_outlier_strength": 0.0,
                "note": "Error-level analysis only works on JPEG files, so it was skipped for this format."}

    q = quality or original_q
    rgb = img.convert("RGB")

    # Screenshots, logos and flat graphics are mostly perfectly flat colour with sharp edges; ELA reacts to
    # those edges and would call them edited. Skip them rather than raise a false alarm.
    gray = np.array(rgb.convert("L")).astype(np.float32)
    edge = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1])) + np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    flat_fraction = float((edge <= 1.0).mean())
    if flat_fraction > 0.6:
        return {"applicable": False, "splicing_detected": False, "outlier_blocks": 0, "max_outlier_strength": 0.0,
                "note": "This looks like a screenshot or flat graphic, where error-level analysis is unreliable, so it was skipped."}
    buffer = io.BytesIO()
    rgb.save(buffer, "JPEG", quality=int(q))
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    diff = np.array(ImageChops.difference(rgb, recompressed)).astype(np.float32).mean(axis=2)

    h, w = diff.shape
    bh, bw = max(h // GRID, 1), max(w // GRID, 1)
    means: List[float] = []
    for i in range(GRID):
        for j in range(GRID):
            d = diff[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw]
            if d.size:
                means.append(float(d.mean()))
    block_arr = np.array(means) if means else np.zeros(1)

    z = _robust_z(block_arr, floor=0.08)
    median_level = float(np.median(block_arr))
    # A flagged block must stand out statistically AND be clearly above the quiet background in absolute terms.
    flagged = (z > 8.0) & (block_arr > max(ABS_FLOOR, 4.0 * median_level))
    outlier_blocks = int(flagged.sum())
    max_strength = float(z.max())

    # A pasted/edited area is local: a few blocks stand out, not half the picture.
    splicing = 1 <= outlier_blocks <= (GRID * GRID) // 6

    return {
        "applicable": True,
        "estimated_jpeg_quality": original_q,
        "mean_error_level": round(float(diff.mean()), 3),
        "max_error_level": round(float(diff.max()), 2),
        "block_variance": round(float(block_arr.std()), 3),
        "block_range": round(float(block_arr.max() - block_arr.min()), 3),
        "outlier_blocks": outlier_blocks,
        "max_outlier_strength": round(max_strength, 1),
        "splicing_detected": bool(splicing),
    }


def detect_image_manipulation(file_path: Path, img: Image.Image, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Looks for pasted-in or locally edited regions and for editing-software tags."""
    indicators: List[str] = []
    suspicion_score = 8.0  # clean baseline

    ela_result = perform_error_level_analysis(img)
    if ela_result.get("splicing_detected"):
        strength = ela_result["max_outlier_strength"]
        indicators.append(
            f"{ela_result['outlier_blocks']} small region(s) react to re-compression very differently "
            "from the rest of the picture, which can mean they were pasted in or edited separately"
        )
        # stronger outliers push the score higher, but ELA alone is never treated as proof
        suspicion_score += min(30.0 + (strength - 8.0) * 0.6, 44.0)

    editing = (metadata or {}).get("editing_signatures", [])
    if editing:
        indicators.extend(editing)
        suspicion_score += 35.0  # edited, but editing alone is not proof of deception

    manipulated = suspicion_score >= 60.0

    if ela_result.get("applicable") and not ela_result.get("splicing_detected"):
        indicators.append("Compression looks consistent across the image (no pasted-in region found by error-level analysis)")
    elif not ela_result.get("applicable"):
        indicators.append(ela_result.get("note", "Error-level analysis was not applicable to this file."))

    return {
        "manipulation_score": round(min(suspicion_score, 95.0), 1),
        "is_manipulated": manipulated,
        "indicators": indicators,
        "ela": ela_result,
    }
