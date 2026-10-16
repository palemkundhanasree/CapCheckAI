# CapCheck AI — Multi-Modal Fact-Checking & Deepfake Verification Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Node: 18+](https://img.shields.io/badge/Node.js-18%20%7C%2020%20%7C%2022-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-61dafb.svg)](https://react.dev/)

> **CapCheck AI** is an end-to-end, multi-modal verification suite designed to address modern online misinformation, synthetic media, and out-of-context recycled media. 
>
> Unlike black-box tools that emit a single ambiguous "percentage fake", CapCheck AI distinctly separates **factual veracity**, **physical media synthesis**, and **deceptive contextual framing**.

---

## 1. The Core Problem & Our Three-Pillar Architecture

Online deception operates across three fundamentally distinct vectors that traditional tools conflate:

```
                                  CAPCHECK AI VERIFICATION
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 ▼                            ▼                            ▼
       [ PILLAR 1: VERACITY ]       [ PILLAR 2: AUTHENTICITY ]    [ PILLAR 3: CONTEXT ]
   Is the factual claim supported?   Was the media AI-generated?   Is authentic media recycled
   • Independent News Registries     • 2D FFT Frequency Decay      with a deceptive caption
   • Curated IFCN Fact-Checks        • JPEG Error Level Analysis   or altered timestamp?
   • Wikipedia Knowledge Base        • Vocoder ZCR / Audio Phase   • EXIF Hardware & Dates
   • Lexical Stance Matching         • C2PA Content Credentials    • Provenance Manifests
```

1. **Is the factual claim supported by available evidence?** An authentic, unedited photograph can still be shared alongside a completely fabricated claim.
2. **Does the media show signs of being AI-generated or manipulated?** A real event can be depicted using a synthetic diffusion image or cloned voice.
3. **Is the media being presented in a misleading or incorrect context?** Real footage from 2016 can be recycled and falsely claimed as breaking news today.

---

## 2. Multi-Modal Verification Capabilities

### 📝 Text Claim Verification
- Accepts factual statements, statistics, or viral quotes.
- Automatically isolates key factual assertions and named entities.
- Queries Google FactCheck Tools API and curated IFCN fact-check databases.
- Performs bidirectional lexical and stance matching (Supports, Contradicts, Context, Neutral).

### 🌐 News Article URL Ingestion
- Ingests public news articles safely through an SSRF-hardened web crawler.
- Extracts article headlines, authors, publish dates, and body text.
- Cross-references publisher domains against reputation registries.

### 🖼️ Image Forensics
- **2D Fast Fourier Transform (FFT)**: Detects high-frequency periodic grid artifacts left by latent diffusion upsamplers (Stable Diffusion, Midjourney, DALL-E).
- **Error Level Analysis (ELA)**: Re-quantizes images at 95% quality to detect compression anomalies and spliced regions.
- **Sensor PRNU Residuals**: Compares inter-channel photon noise correlation typical of physical CMOS/CCD optical sensors.
- **C2PA Content Credentials**: Parses cryptographic JUMBF manifests from the Coalition for Content Provenance and Authenticity.

### 🎥 Video Deepfake & Temporal Analysis
- Keyframe sampling across the video timeline without saturating system RAM.
- **Temporal Consistency**: Measures inter-frame illumination variance and face-swap boundary flickering.
- **Audio Stream Extraction**: Demuxes audio and routes it directly to speech forensics.
- **Lip-Sync Consistency**: Analyzes phoneme energy against facial frame motion.

### 🎙️ Audio & Voice Cloning Detection
- **Acoustic Profiling**: Measures Zero-Crossing Rate (ZCR) and dynamic range compression.
- **Text-to-Speech Detection**: Inspects vocoder phase anomalies and TTS metadata signatures (ElevenLabs, Tortoise, Bark).
- **Speaker Consistency**: Evaluates timbre stability across speech intervals.
- **Speech-to-Text Transcription**: Generates timestamped transcripts and cross-verifies spoken factual assertions against fact registries.

---

## 3. Quick Start on Windows (1-Click Launchers)

### Step 1: Install Dependencies
Double-click **`install.bat`** (or run via Command Prompt):
```cmd
install.bat
```
*What this does:*
- Verifies Python (3.10+) and Node.js are available in system PATH.
- Creates a dedicated Python virtual environment in `venv\`.
- Installs backend dependencies (`fastapi`, `pillow`, `numpy`, `sqlalchemy`, `reportlab`, etc.).
- Installs frontend packages (`npm install`) and builds production-optimized assets.
- Creates `.env` and initializes the local SQLite database.

### Step 2: Launch Application
Double-click **`run.bat`**:
```cmd
run.bat
```
*What this does:*
- Starts the FastAPI backend server on `http://127.0.0.1:8000`.
- Starts the Vite frontend on `http://localhost:5173`.
- Automatically tests service health and opens your default browser when ready.

### Step 3: Stop Application
To cleanly terminate services, double-click **`stop.bat`**.

---

## 4. Manual Installation & CLI Execution

### Backend Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 2. Install requirements
pip install -r backend/requirements.txt

# 3. Initialize SQLite database
python -c "import sys; sys.path.insert(0, 'backend'); from app.db.session import init_db; init_db()"

# 4. Start FastAPI server
set PYTHONPATH=backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 5. Docker Deployment

CapCheck AI is packaged with a multi-stage production Docker configuration:
```bash
# Build and run container
docker-compose up --build
```
The application will be accessible at `http://localhost:8000`.

---

## 6. Interactive Demo Test Bench

CapCheck AI includes built-in real-world test cases ready for 1-click evaluation on the Home and Verify pages:

| Test Case | Category | Expected Verdict |
| :--- | :--- | :--- |
| **Pope Francis Balenciaga Puffer** | Image Claim | *AI-Generated Media Detected* |
| **Drinking Bleach COVID Cure** | Medical Rumor | *Contradicted / Likely False* |
| **Apollo 11 Moon Landing Staged** | Historical Hoax | *Contradicted / Likely False* |
| **Great Wall Visible from Space** | Popular Myth | *Misleading or Missing Context* |
| **5G Cell Towers Killing Birds** | Viral Claim | *Contradicted / Likely False* |

---

## 7. Security & Privacy Architecture

- **SSRF Defense**: Strict validation of URL schemes (`http`, `https`). Prohibits loopback (`127.0.0.0/8`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP metadata (`169.254.169.254`).
- **File Integrity & Magic Bytes**: Files are inspected at binary header level to prevent extension spoofing and decompression bombs.
- **Ephemeral Storage**: Uploaded files receive cryptographically random UUID names. The server automatically sweeps and shreds uploads older than 48 hours.
- **Immediate User Deletion**: The user can click "Delete & Shred Media" on any dossier to atomically unlink and wipe all associated temporary media.

---

## 8. Directory Structure

```
capcheck-ai/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/routes/      # Home, Verify, Results, History, About, Privacy, Admin
│   │   ├── components/      # VerdictCard, ConfidenceMeter, EvidenceCard, Forensics
│   │   ├── services/        # API client, verification API, demo presets
│   │   └── types/           # TypeScript interfaces
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/             # Health, claims, news, images, videos, audio, reports, admin
│   │   ├── db/              # SQLAlchemy models, session, repositories
│   │   ├── engines/
│   │   │   ├── news/        # Article & claim extractors, factcheck client, stance matcher
│   │   │   ├── image/       # 2D FFT, ELA, C2PA, EXIF, sensor noise
│   │   │   ├── video/       # Keyframe extractor, temporal jitter, lip sync
│   │   │   └── audio/       # Acoustic ZCR, vocoder detection, Whisper transcription
│   │   ├── security/        # SSRF defense, file validation, rate limiter, retention
│   │   └── services/        # Orchestrator, verdict engine, confidence calculator
│   └── requirements.txt
│
├── ml/
│   ├── model_registry/      # Registry metadata and active models
│   ├── model_cards/         # Documentation of 2D FFT, ELA, and Acoustic detectors
│   └── evaluation/          # Precision, Recall, F1 metrics
│
├── tests/                   # Pytest test suites (unit, security, news, api)
├── docs/                    # Architecture, workflow, api, privacy, evaluation
├── install.bat              # Windows automated installer
├── run.bat                  # Windows dual-service launcher
├── run_backend.bat          # Windows backend launcher
├── run_frontend.bat         # Windows frontend launcher
├── stop.bat                 # Windows service terminator
├── Dockerfile               # Production multi-stage Docker build
├── docker-compose.yml       # Container orchestration
└── README.md
```

---

## 9. Running Tests

Execute the comprehensive test suite using pytest:
```bash
set PYTHONPATH=backend
pytest tests/ -v
```

---

## 10. License
This project is licensed under the [MIT License](LICENSE).
