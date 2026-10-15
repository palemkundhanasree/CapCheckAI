# CapCheck AI — Input-to-Result Workflow

This document traces the complete execution lifecycle of a verification job in CapCheck AI from user submission to report generation and optional file shredding.

```
[ User Input ]
   │
   ├── (Claim) ────► Extract Claims ───► Query FactCheck & Wikipedia ──► Stance Scoring ──┐
   ├── (News URL) ─► SSRF Safe Fetch ──► Parse Article Body & Claims ──► Cross-Check ─────┤
   ├── (Image) ────► Validate Header ──► 2D FFT & ELA Forensics ───────► EXIF / C2PA ─────┼─► [ Verdict Engine ]
   ├── (Video) ────► Sample Frames ────► Temporal Jitter Forensics ────► Audio Track ─────┤        │
   └── (Audio) ────► Waveform / ZCR ───► Vocoder Synthetic Detect ─────► Transcribe ──────┘        │
                                                                                                   ▼
                                                                                         [ 3-Pillar Synthesis ]
                                                                                                   │
                                                                                                   ├── Factual Veracity
                                                                                                   ├── Media Authenticity
                                                                                                   └── Contextual Framing
                                                                                                   │
                                                                                                   ▼
                                                                                         [ Store to SQLite DB ]
                                                                                                   │
                                                                                                   ▼
                                                                                         [ PDF / Web Dossier ]
```

## Detailed Execution Phases

### Phase 1: Ingestion & Security Screening
1. The client submits input via multipart/form-data or application/json to `/api/v1/verify/{type}`.
2. The Rate Limiter checks the client IP against the sliding-window budget.
3. If an upload is submitted:
   - File size is checked against configured limits (Image: 25MB, Video: 150MB, Audio: 50MB).
   - Magic bytes are inspected to prevent MIME spoofing.
   - The file is saved to `storage/uploads/` with a non-guessable UUID filename.
4. A `VerificationJob` record is created in status `queued` (progress: 0%) and the job ID is immediately returned to the client.

### Phase 2: Asynchronous Orchestration
1. A background worker thread retrieves the job and begins processing:
   - Progress 15%: Initial extraction and parsing.
   - Progress 35%: Knowledge retrieval & metadata parsing.
   - Progress 55%: Algorithmic forensics & spectral analysis.
   - Progress 75%: Evidence ranking & source credibility weighting.
   - Progress 90%: Synthesis of the 3-pillar verdict and confidence index.
2. The client polls `GET /api/v1/jobs/{job_id}` at 1.2-second intervals, visualizing each stage transition.

### Phase 3: Evidence Evaluation & Verdict Synthesis
1. The Verdict Engine independently scores:
   - **Factual Veracity**: Weighs supporting credibility vs. contradicting credibility.
   - **Media Authenticity**: Evaluates high-frequency spectral ratios, ELA differences, and acoustic ZCR.
   - **Context Integrity**: Compares EXIF capture dates and claim framing.
2. The Confidence Service computes the final score based on evidence quantity, stance consensus, and forensic distance.

### Phase 4: Dossier Delivery & Data Lifecycle
1. The completed `Report` and `EvidenceItem` rows are written to the database.
2. The job status transitions to `completed` with a reference to the `report_id`.
3. The client receives the completion signal and navigates to `/results/{report_id}`.
4. The user may download an official PDF dossier via `/api/v1/reports/{report_id}/pdf`.
5. Upon user request (`DELETE /api/v1/reports/{report_id}`), all associated files are permanently unlinked and shredded from disk.
