from pathlib import Path
from typing import Dict, Any, List


def inspect_audio_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Inspects audio file tags and comments for text-to-speech encoder signatures.
    """
    signatures: List[str] = []
    metadata = {
        "encoder": None,
        "is_synthetic_tag_found": False,
        "signatures": signatures
    }

    try:
        with open(file_path, "rb") as f:
            chunk = f.read(65536)  # Read first 64KB

            # Look for common AI voice and TTS generator signatures
            tts_markers = [
                (b"ElevenLabs", "ElevenLabs Voice Synthesis"),
                (b"Tortoise", "Tortoise TTS Model"),
                (b"Bark", "Suno Bark Audio Model"),
                (b"Coqui", "Coqui TTS Engine"),
                (b"openai", "OpenAI Audio Engine"),
                (b"gTTS", "Google Text-To-Speech"),
                (b"pyttsx3", "Python TTS Library")
            ]

            for marker, description in tts_markers:
                if marker.lower() in chunk.lower():
                    signatures.append(f"Synthetic speech engine signature identified: {description}")
                    metadata["is_synthetic_tag_found"] = True
                    metadata["encoder"] = description

    except Exception:
        pass

    return metadata
