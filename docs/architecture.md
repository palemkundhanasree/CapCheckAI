# CapCheck AI — System Architecture & Module Responsibilities

## 1. High-Level Architecture

CapCheck AI is engineered as an enterprise-grade, multi-modal fact verification and media forensic suite. The system consists of a decoupled frontend, a high-throughput FastAPI asynchronous application server, modular forensic analysis engines, an SQLite/PostgreSQL-compatible SQLAlchemy database layer, and safe ephemeral storage.

```
                           +---------------------------+
                           |   CapCheck AI Frontend    |
                           |  React + Vite + Tailwind  |
                           +-------------+-------------+
                                         | REST API (HTTP / JSON / Multi-part)
                                         v
                           +---------------------------+
                           |    FastAPI API Gateway    |
                           |  (Rate Limiting & SSRF)   |
                           +-------------+-------------+
                                         |
                 +-----------------------+-----------------------+
                 |                       |                       |
                 v                       v                       v
        +-----------------+     +-----------------+     +-----------------+
        |  Verification   |     |    Database     |     |   Safe Storage  |
        |  Orchestrator   |     |  (SQLAlchemy /  |     |  (UUID Paths /  |
        |                 |     |     SQLite)     |     |   Auto-Purge)   |
        +--------+--------+     +-----------------+     +-----------------+
                 |
   +-------------+-------------+-------------+-------------+
   |             |             |             |             |
   v             v             v             v             v
+------+     +-------+     +-------+     +-------+     +-------+
| News |     | Image |     | Audio |     | Video |     |Verdict|
|Engine|     |Forens.|     |Forens.|     |Forens.|     |Engine |
+------+     +-------+     +-------+     +-------+     +-------+
```

## 2. Core Modules & Responsibilities

### A. API Gateway & Security (`backend/app/api/` & `security/`)
- **Rate Limiting**: Sliding-window token limiter per client IP preventing denial of service.
- **SSRF Defense**: Validates URL scheme, performs recursive DNS resolution, and rejects all RFC 1918 / loopback / link-local addresses (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`).
- **File Validation**: Enforces magic byte signatures, strict file extensions, and limits on decompression ratios.
- **Retention & Shredding**: Ephemeral file isolation with automatic 48-hour purge and user-initiated atomic disk deletion.

### B. Forensic & Verification Engines (`backend/app/engines/`)
1. **News & Claim Engine**:
   - `claim_extractor.py`: Extracts verifiable factual assertions and named entities.
   - `factcheck_client.py`: Integrates Google FactCheck Tools API and curated IFCN fact-check database.
   - `search_client.py`: Interfaces with Wikipedia API and web knowledge indices.
   - `source_registry.py`: Maintains credibility ratings for over 50 mainstream news outlets and fact-checkers.
   - `claim_matcher.py`: Determines lexical and semantic stance (SUPPORTS, CONTRADICTS, NEUTRAL, CONTEXT).

2. **Image Forensic Engine**:
   - `image_validator.py`: Safe header validation and decompression bomb prevention.
   - `metadata_reader.py`: EXIF camera make/model parsing and generative AI software chunk detection.
   - `provenance_checker.py`: C2PA Content Credentials and CAI manifest verification.
   - `ai_image_detector.py`: 2D Fast Fourier Transform (FFT) spatial frequency analysis and sensor PRNU noise residual correlation.
   - `manipulation_detector.py`: Error Level Analysis (ELA) for localized JPEG tampering.
   - `similarity_search.py`: Perceptual difference hashing (dHash) and average hashing (aHash).

3. **Audio Forensic Engine**:
   - `audio_validator.py`: Safe container and codec inspection.
   - `audio_preprocessor.py`: Waveform analysis, zero-crossing rate (ZCR), and dynamic range calculation.
   - `synthetic_audio_detector.py`: Vocoder phase anomaly and acoustic dynamic range compression detection.
   - `speech_transcriber.py`: Speech-to-text transcription with timestamped segmentation.
   - `speech_claim_checker.py`: Cross-checks spoken claims against factual evidence registries.

4. **Video Forensic Engine**:
   - `frame_extractor.py`: Samples keyframes at configurable temporal intervals without loading entire video files into memory.
   - `temporal_analyzer.py`: Measures inter-frame jitter, lighting shifts, and face-swap boundary flickering.
   - `audio_extractor.py`: Routes the audio track to the speech and audio forensics pipeline.
   - `lip_sync_checker.py`: Evaluates phoneme-viseme correlation.
   - `video_aggregator.py`: Synthesizes frame findings and acoustic evidence into a unified score.

### C. The Three-Pillar Verdict Engine (`backend/app/services/verdict_engine.py`)
Distinguishes three separate questions:
1. **Factual Claim Veracity**: Supported vs. Contradicted vs. Misleading Context.
2. **Media Physical Authenticity**: Authentic vs. AI-Generated vs. Manipulated.
3. **Contextual Integrity**: Accurate Context vs. Out of Context.

### D. Data Layer (`backend/app/db/`)
- Relational schema modeling `VerificationJob`, `Report`, `EvidenceItem`, `MediaAnalysis`, and `AuditEvent`.
- Native SQLite support for zero-configuration local execution, fully compatible with PostgreSQL.
