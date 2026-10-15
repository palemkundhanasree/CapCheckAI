from pathlib import Path
from PIL import Image
from app.engines.image.ai_image_detector import detect_ai_generation
from app.engines.image.manipulation_detector import detect_image_manipulation
from app.engines.image.similarity_search import find_similar_images_fingerprint
from app.config import settings


def test_image_forensics_pipeline():
    test_img_path = settings.TEMP_DIR / "test_img.jpg"
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    img.save(test_img_path, "JPEG")

    ai_res = detect_ai_generation(test_img_path, img)
    assert "ai_generated_score" in ai_res
    assert isinstance(ai_res["is_ai_generated"], bool)

    manip_res = detect_image_manipulation(test_img_path, img)
    assert "manipulation_score" in manip_res
    assert "ela" in manip_res

    similarity = find_similar_images_fingerprint(img)
    assert "dhash" in similarity
    assert "ahash" in similarity

    # Cleanup
    if test_img_path.exists():
        test_img_path.unlink()
