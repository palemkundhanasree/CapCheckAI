from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image


def compute_difference_hash(img: Image.Image, hash_size: int = 8) -> str:
    """Computes 64-bit perceptual difference hash (dHash)."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    arr = np.array(resized)
    # Compare adjacent pixels
    diff = arr[:, 1:] > arr[:, :-1]
    # Convert bool array to hex string
    hex_str = "".join([f"{int(''.join(['1' if v else '0' for v in row]), 2):02x}" for row in diff])
    return hex_str


def compute_average_hash(img: Image.Image, hash_size: int = 8) -> str:
    """Computes 64-bit average hash (aHash)."""
    resized = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    arr = np.array(resized)
    avg = arr.mean()
    bits = (arr > avg).flatten()
    hex_str = f"{int(''.join(['1' if b else '0' for b in bits]), 2):016x}"
    return hex_str


def find_similar_images_fingerprint(img: Image.Image) -> Dict[str, Any]:
    """Generates visual fingerprint hashes for duplicate and context lookup."""
    dhash = compute_difference_hash(img)
    ahash = compute_average_hash(img)
    return {
        "dhash": dhash,
        "ahash": ahash,
        "search_status": "Visual fingerprint generated successfully"
    }
