"""
Calibration checks for the image detectors using synthetic pictures whose ground truth is known.
These guard against two failure modes found during tuning: detectors that never fire (thresholds far above
anything real) and detectors that flag ordinary photos.
"""
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, PngImagePlugin

from app.engines.image.ai_image_detector import analyze_frequency_domain_artifacts, detect_ai_generation
from app.engines.image.manipulation_detector import estimate_jpeg_quality, perform_error_level_analysis
from app.engines.image.metadata_reader import read_image_metadata


def scene(seed, size=(800, 600)):
    rng = np.random.default_rng(seed)
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        img[..., c] = 110 + 50 * np.sin(xx / (40 + 10 * c) + seed) + 35 * np.cos(yy / (30 + 7 * c))
    tex = rng.normal(0, 25, (h, w, 3))
    tex = np.array(Image.fromarray(np.clip(tex + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) - 128
    img[h // 3:] += tex[h // 3:] * 1.6
    img[:h // 3] = img[:h // 3] * 0.3 + 170
    img += rng.normal(0, 3, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def jpeg(img, q):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=q)
    b.seek(0)
    return Image.open(b)


def test_jpeg_quality_is_read_back_exactly():
    for q in (50, 75, 85, 95):
        assert estimate_jpeg_quality(jpeg(scene(1), q)) == q


def test_pasted_region_is_flagged_and_clean_photo_is_not():
    hits, false_alarms = 0, 0
    for seed in range(6):
        base = jpeg(scene(seed), 85).convert("RGB")
        clean = jpeg(base, 85)
        donor = jpeg(scene(seed + 50), 45).convert("RGB")
        spliced = base.copy()
        spliced.paste(donor.crop((200, 250, 420, 420)), (300, 300))
        spliced = jpeg(spliced, 85)
        hits += perform_error_level_analysis(spliced)["splicing_detected"]
        false_alarms += perform_error_level_analysis(clean)["splicing_detected"]
    assert hits == 6
    assert false_alarms == 0


def test_ela_is_skipped_for_png_and_for_flat_graphics():
    buf = io.BytesIO()
    scene(1).save(buf, "PNG")
    buf.seek(0)
    assert perform_error_level_analysis(Image.open(buf))["applicable"] is False

    from PIL import ImageDraw
    flat = Image.new("RGB", (800, 600), "white")
    ImageDraw.Draw(flat).rectangle([100, 100, 500, 400], fill=(30, 90, 200))
    assert perform_error_level_analysis(jpeg(flat, 92))["applicable"] is False


def test_periodic_upsampling_grid_is_detected_but_normal_photos_are_not():
    cam = scene(3)
    a = np.array(cam).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    gridded = np.clip(a + (6 * np.cos(2 * np.pi * xx / 4.0) * np.cos(2 * np.pi * yy / 4.0))[..., None], 0, 255).astype(np.uint8)
    gray = lambda im: np.array(im.convert("L")).astype(np.float32)
    assert analyze_frequency_domain_artifacts(gray(Image.fromarray(gridded)))["abnormal_frequency_spectrum"] is True
    for q in (60, 90):
        assert analyze_frequency_domain_artifacts(gray(jpeg(cam, q)))["abnormal_frequency_spectrum"] is False


def test_caption_containing_steps_or_seed_is_not_treated_as_ai_metadata(tmp_path: Path):
    img = Image.fromarray(np.random.default_rng(0).integers(0, 255, (300, 300, 3), dtype=np.uint8))
    info = PngImagePlugin.PngInfo()
    info.add_text("Description", "Two steps from home, the seed of an idea")
    p = tmp_path / "innocent.png"
    img.save(p, pnginfo=info)
    assert read_image_metadata(p, Image.open(p))["generator_signatures"] == []


def test_stable_diffusion_parameters_chunk_is_detected(tmp_path: Path):
    img = Image.fromarray(np.random.default_rng(0).integers(0, 255, (300, 300, 3), dtype=np.uint8))
    info = PngImagePlugin.PngInfo()
    info.add_text("parameters", "a cat, Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 1")
    p = tmp_path / "sd.png"
    img.save(p, pnginfo=info)
    opened = Image.open(p)
    meta = read_image_metadata(p, opened)
    assert meta["generator_signatures"]
    assert detect_ai_generation(p, opened, metadata=meta)["ai_generated_score"] >= 90
