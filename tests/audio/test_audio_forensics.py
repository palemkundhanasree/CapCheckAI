from pathlib import Path
from app.engines.audio.synthetic_audio_detector import detect_synthetic_speech
from app.engines.audio.voice_deepfake_detector import detect_voice_cloning_deepfake
from app.engines.audio.speaker_consistency import evaluate_speaker_consistency
from app.engines.audio.speech_transcriber import transcribe_audio_file
from app.config import settings


def test_audio_forensics_synthetic_detect():
    waveform_features = {
        "dynamic_range_db": 9.5,  # Artificially compressed
        "energy_variance": 0.002,
        "zero_crossing_rate": 0.04
    }
    metadata = {
        "is_synthetic_tag_found": True,
        "encoder": "ElevenLabs Voice Synthesis"
    }

    syn_res = detect_synthetic_speech(waveform_features, metadata)
    assert syn_res["is_synthetic"] is True
    assert syn_res["synthetic_voice_probability"] >= 50.0

    clone_res = detect_voice_cloning_deepfake(syn_res, waveform_features)
    assert clone_res["voice_cloning_detected"] is True

    consistency = evaluate_speaker_consistency(waveform_features)
    assert "speaker_consistency_score" in consistency


def test_speech_transcriber_fallback():
    dummy_audio_path = settings.TEMP_DIR / "dummy_audio.wav"
    with open(dummy_audio_path, "wb") as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

    result = transcribe_audio_file(dummy_audio_path)
    assert "full_transcript" in result
    assert "segments" in result

    if dummy_audio_path.exists():
        dummy_audio_path.unlink()
