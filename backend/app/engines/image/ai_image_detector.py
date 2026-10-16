from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image, ImageFilter


def analyze_frequency_domain_artifacts(img_gray: np.ndarray) -> Dict[str, Any]:
    """
    Looks for sharp, isolated peaks in the 2D Fourier spectrum. Neural-network upsampling (transposed
    convolutions, nearest-neighbour + conv decoders) tends to leave a regular lattice that shows up as spikes.

    Natural photos have a smooth, falling spectrum, so the average falloff with distance from the centre is
    removed first and only what sticks out above it is measured (in robust standard deviations). On test
    images, ordinary photos (JPEG at several qualities, PNG, upscaled) peaked at about 3 while an injected
    upsampling lattice peaked at about 10.
    """
    h, w = img_gray.shape
    window = np.outer(np.hanning(h), np.hanning(w))  # stops the image border from creating fake peaks
    centred = (img_gray - img_gray.mean()) * window
    magnitude = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(centred))))

    yy, xx = np.indices(magnitude.shape)
    dy, dx = yy - h // 2, xx - w // 2
    radius = np.hypot(dy, dx)
    bins = radius.astype(int)
    radial_mean = np.bincount(bins.ravel(), magnitude.ravel()) / np.maximum(np.bincount(bins.ravel()), 1)
    residual = magnitude - radial_mean[bins]

    short_side = min(h, w)
    band = (radius > 0.06 * short_side) & (radius < 0.48 * short_side) & (np.abs(dx) > 3) & (np.abs(dy) > 3)
    values = residual[band]
    if values.size == 0:
        return {"peak_strength": 0.0, "strong_peak_count": 0, "peak_spike_ratio": 0.0, "abnormal_frequency_spectrum": False}
    median = float(np.median(values))
    sigma = 1.4826 * float(np.median(np.abs(values - median))) + 1e-6
    z = (values - median) / sigma
    peak_strength = float(z.max())
    strong = int((z > 10.0).sum())

    return {
        "peak_strength": round(peak_strength, 1),
        "strong_peak_count": strong,
        "peak_spike_ratio": round(peak_strength, 2),  # kept under the old key for stored reports / the UI
        "abnormal_frequency_spectrum": bool(peak_strength >= 7.0),
    }


def analyze_sensor_noise_distribution(img_rgb: Image.Image) -> Dict[str, Any]:
    """
    Analyzes optical sensor noise vs synthetic smoothing.
    Real camera photos exhibit natural photon shot noise across RGB channels.
    """
    img_arr = np.array(img_rgb).astype(np.float32)
    blurred = np.array(img_rgb.filter(ImageFilter.GaussianBlur(radius=1.2))).astype(np.float32)
    noise_residual = img_arr - blurred

    r_var = float(np.var(noise_residual[:, :, 0]))
    g_var = float(np.var(noise_residual[:, :, 1]))
    b_var = float(np.var(noise_residual[:, :, 2]))
    avg_var = (r_var + g_var + b_var) / 3.0

    flat_r = noise_residual[:, :, 0].flatten()
    flat_g = noise_residual[:, :, 1].flatten()
    corr_matrix = np.corrcoef(flat_r, flat_g)
    cross_corr = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.5

    # Check for artificial plastic/wax smoothing across skin/surfaces
    is_unnaturally_smooth = avg_var < 0.8 and cross_corr < 0.2

    return {
        "channel_noise_variance": {"red": round(r_var, 2), "green": round(g_var, 2), "blue": round(b_var, 2)},
        "average_noise_variance": round(avg_var, 2),
        "sensor_noise_correlation": round(cross_corr, 3),
        "is_unnaturally_smooth": is_unnaturally_smooth
    }


def detect_ai_generation(file_path: Path, img: Image.Image, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Accurately determines if an image is AI-generated (Midjourney, DALL-E, Stable Diffusion)
    versus captured by a real camera, with calibrated thresholds to prevent false positives.
    """
    indicators: List[str] = []
    suspicion_score = 10.0  # Default low baseline for clean real camera photos

    # 1. Direct Metadata Signatures (100% reliable when present)
    meta = metadata or {}
    gen_signatures = meta.get("generator_signatures", [])
    if gen_signatures:
        for sig in gen_signatures:
            indicators.append(sig)
        suspicion_score = 96.0

    # Check filename indicators for generated exports
    fname_lower = file_path.name.lower()
    if any(k in fname_lower for k in ["midjourney", "stablediffusion", "dalle", "dall-e", "comfyui", "flux_"]):
        indicators.append(f"Filename contains AI generation token ({file_path.name})")
        suspicion_score = max(suspicion_score, 88.0)

    # 2. Camera Hardware Provenance Discount
    # If photo has genuine camera EXIF (iPhone, Sony, Canon, Nikon), reduce false positives
    has_real_camera = bool(meta.get("camera_make") or meta.get("camera_model"))
    if has_real_camera and not gen_signatures:
        camera_name = f"{meta.get('camera_make', '')} {meta.get('camera_model', '')}".strip()
        indicators.append(f"Authentic camera hardware tags detected ({camera_name})")
        suspicion_score = max(suspicion_score - 15.0, 5.0)

    # 3. Frequency & noise analysis (always measured from the actual pixels)
    analysis_img = img.convert("RGB")
    if analysis_img.width > 800 or analysis_img.height > 800:
        analysis_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    img_gray = np.array(analysis_img.convert("L")).astype(np.float32)
    freq_stats = analyze_frequency_domain_artifacts(img_gray)
    noise_stats = analyze_sensor_noise_distribution(analysis_img)

    if not gen_signatures and suspicion_score < 70.0:
        if freq_stats["abnormal_frequency_spectrum"]:
            indicators.append("Regular repeating pattern in the image spectrum, typical of neural-network upsampling "
                              "(can also come from fences, fabric or screens)")
            suspicion_score += 30.0 + (10.0 if freq_stats["strong_peak_count"] >= 3 else 0.0)
        if noise_stats["is_unnaturally_smooth"]:
            if has_real_camera:
                indicators.append("Very smooth image with almost no sensor noise (a camera is named in the metadata, so this may be heavy noise reduction)")
                suspicion_score += 10.0
            else:
                indicators.append("Unnaturally smooth image with almost no camera sensor noise")
                suspicion_score += 25.0

    # 4. Weak hint: generators output fixed sizes (multiples of 64, usually 512 and up) and strip camera data.
    no_exif = not meta.get("has_exif") and not has_real_camera
    if (not gen_signatures and no_exif and img.width % 64 == 0 and img.height % 64 == 0
            and min(img.width, img.height) >= 512):
        indicators.append(f"Size {img.width}x{img.height} is a typical AI-generator output size and there is no camera data (weak hint only)")
        suspicion_score += 12.0

    # Final score calibration
    final_score = round(min(max(suspicion_score, 5.0), 98.0), 1)
    is_ai = final_score >= 60.0

    if not is_ai and not indicators:
        indicators.append("No AI-generation signs found by the automated tests (this does not prove the image is genuine)")

    return {
        "ai_generated_score": final_score,
        "is_ai_generated": is_ai,
        "indicators": indicators,
        "frequency_analysis": freq_stats,
        "noise_analysis": noise_stats
    }
