from pathlib import Path
from typing import Tuple, Dict, Any
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, status


def validate_image_file(file_path: Path) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Validates that the file is a readable image and not corrupted or a decompression bomb.
    Returns (PIL Image, basic stats).
    """
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found.")

    try:
        # Prevent decompression bombs
        Image.MAX_IMAGE_PIXELS = 50_000_000
        img = Image.open(file_path)
        img.verify()  # Verifies integrity without decoding entire image

        # Re-open for actual usage after verify
        img = Image.open(file_path)
        stats = {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "megapixels": round((img.width * img.height) / 1_000_000, 2),
            "animated": getattr(img, "is_animated", False)
        }

        if img.width < 10 or img.height < 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image dimensions are too small for forensic analysis.")

        return img, stats
    except UnidentifiedImageError:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unrecognized or corrupted image file format.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Image validation failed: {str(e)}")
