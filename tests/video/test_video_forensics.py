from pathlib import Path
from PIL import Image
from app.engines.video.temporal_analyzer import analyze_temporal_consistency
from app.engines.video.lip_sync_checker import check_lip_sync_consistency
from app.engines.video.video_aggregator import aggregate_video_findings
from app.config import settings


def test_video_temporal_and_aggregation():
    # Create two test frames
    f1_path = settings.TEMP_DIR / "f1.jpg"
    f2_path = settings.TEMP_DIR / "f2.jpg"
    Image.new("RGB", (100, 100), (50, 50, 50)).save(f1_path)
    Image.new("RGB", (100, 100), (55, 55, 55)).save(f2_path)

    temporal = analyze_temporal_consistency([f1_path, f2_path])
    assert "temporal_inconsistency_score" in temporal

    lip_sync = check_lip_sync_consistency(has_audio=True, frame_results=[{"is_suspicious": False}])
    assert "lip_sync_status" in lip_sync

    agg = aggregate_video_findings(
        meta={"fps": 30.0},
        frame_analyses=[{"artifact_score": 15.0}],
        temporal_res=temporal,
        audio_analysis={"synthetic_voice_probability": 20.0, "is_synthetic": False},
        lip_sync_res=lip_sync
    )
    assert "deepfake_score" in agg
    assert "is_deepfake" in agg

    # Cleanup
    f1_path.unlink(missing_ok=True)
    f2_path.unlink(missing_ok=True)
