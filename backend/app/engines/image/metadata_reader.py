from pathlib import Path
from typing import Dict, Any
from PIL import Image, ExifTags


def read_image_metadata(file_path: Path, img: Image.Image) -> Dict[str, Any]:
    """
    Extracts EXIF metadata, camera hardware details, and generator software tags.
    """
    metadata: Dict[str, Any] = {
        "has_exif": False,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "date_time": None,
        "generator_signatures": [],
        "editing_signatures": [],
        "raw_tags": {}
    }

    # 1. Inspect PIL Info dictionary (PNG text chunks, WebP info).
    # Generic words such as "steps" or "seed" are only meaningful as chunk NAMES (that is how Stable Diffusion
    # tools store them). Matching them inside free text would flag a photo captioned "two steps from home".
    GENERATOR_CHUNK_KEYS = {"parameters", "prompt", "workflow", "sd-metadata", "invokeai_metadata", "negative_prompt"}
    GENERATOR_NAMES = ["stable diffusion", "midjourney", "dall-e", "dall·e", "novelai", "comfyui", "automatic1111",
                       "invokeai", "adobe firefly", "leonardo.ai"]
    if hasattr(img, "info") and isinstance(img.info, dict):
        for k, v in img.info.items():
            if isinstance(v, (bytes, bytearray)):
                continue  # ICC profiles, thumbnails and other binary blobs are not text claims
            k_str = str(k).lower().strip()
            v_str = str(v).lower()
            if k_str in GENERATOR_CHUNK_KEYS or any(name in v_str for name in GENERATOR_NAMES):
                metadata["generator_signatures"].append(f"AI generation metadata detected in chunk '{k}'")
                metadata["software"] = "AI Generative Engine (Embedded Chunk)"

    # 2. Inspect EXIF Data
    try:
        exif_raw = img.getexif()
        if exif_raw:
            metadata["has_exif"] = True
            for tag_id, value in exif_raw.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                # Convert bytes or un-serializable objects to string
                val_str = str(value) if not isinstance(value, (int, float, str)) else value

                if tag_name == "Make":
                    metadata["camera_make"] = str(val_str).strip()
                elif tag_name == "Model":
                    metadata["camera_model"] = str(val_str).strip()
                elif tag_name == "Software":
                    metadata["software"] = str(val_str).strip()
                    # Check for editing software
                    soft_lower = str(val_str).lower()
                    if any(s in soft_lower for s in ["photoshop", "gimp", "lightroom", "affinity", "canva"]):
                        metadata["editing_signatures"].append(f"Image was saved by editing software: {val_str}")
                    elif any(s in soft_lower for s in ["midjourney", "stable diffusion", "dall-e", "adobe firefly"]):
                        metadata["generator_signatures"].append(f"AI generator software signature: {val_str}")
                elif tag_name in ("DateTime", "DateTimeOriginal"):
                    metadata["date_time"] = str(val_str).strip()

                if len(metadata["raw_tags"]) < 20:
                    metadata["raw_tags"][tag_name] = str(val_str)[:100]
    except Exception:
        pass

    return metadata
