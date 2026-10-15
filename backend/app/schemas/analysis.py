from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ImageAnalysisResult(BaseModel):
    is_ai_generated: bool
    ai_generated_probability: float  # 0 to 100
    is_manipulated: bool
    manipulation_probability: float  # 0 to 100
    indicators: List[str] = []
    metadata_checks: Dict[str, Any] = {}
    ela_status: str = "COMPLETED"
    c2pa_present: bool = False
    notes: List[str] = []


class FrameAnalysisResult(BaseModel):
    frame_index: int
    timestamp_seconds: float
    face_detected: bool = False
    artifact_score: float = 0.0
    anomalies: List[str] = []


class VideoAnalysisResult(BaseModel):
    duration_seconds: float
    fps: float
    total_frames_analyzed: int
    deepfake_score: float  # 0 to 100
    temporal_inconsistency_score: float  # 0 to 100
    audio_present: bool
    frames: List[FrameAnalysisResult] = []
    indicators: List[str] = []


class AudioAnalysisResult(BaseModel):
    duration_seconds: float
    sample_rate: int
    channels: int
    transcript: Optional[str] = None
    synthetic_voice_probability: float  # 0 to 100
    voice_cloning_detected: bool
    speaker_consistency_score: float  # 0 to 100
    spectral_artifacts: List[str] = []
    indicators: List[str] = []
