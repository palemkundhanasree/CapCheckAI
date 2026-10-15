# CapCheck AI — REST API Reference (v1)

Base URL: `http://localhost:8000/api/v1`

## Authentication
Admin endpoints require a Bearer JWT token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## 1. System Health & Status

### `GET /health`
Returns system operational state, active forensic modules, and environment flags.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "app_name": "CapCheck AI",
  "version": "1.0.0",
  "environment": "development",
  "demo_mode": true,
  "system": {
    "python_version": "3.11.9",
    "os": "Windows",
    "platform": "Windows-10-10.0.26100-SP0",
    "opencv_available": false,
    "whisper_available": false,
    "google_factcheck_configured": false
  }
}
```

---

## 2. Verification Endpoints

### `POST /verify/claim`
Submit a textual factual assertion for verification.

**Request Body**:
```json
{
  "claim_text": "Drinking disinfectant or bleach is a proven medical cure for coronavirus infections.",
  "context": "Viral posts circulating on social media."
}
```

**Response `202 Accepted`**:
```json
{
  "id": "e229f3d9-93e1-450a-b60b-8531d04423b4",
  "job_type": "claim",
  "status": "queued",
  "progress": 0,
  "current_stage": "Job received and queued",
  "report_id": null,
  "error_message": null,
  "created_at": "2026-10-15T10:00:00Z",
  "updated_at": "2026-10-15T10:00:00Z"
}
```

---

### `POST /verify/url`
Submit a news article or web URL for automated scraping and claim extraction.

**Request Body**:
```json
{
  "url": "https://www.reuters.com/fact-check/sample-claim-article"
}
```

---

### `POST /verify/image`
Upload an image (`multipart/form-data`) for 2D FFT, ELA, and metadata analysis.

**Form Data**:
- `file`: Image file (`.jpg`, `.png`, `.webp`, max 25MB)
- `context`: (Optional) Claimed caption or date context

---

### `POST /verify/video`
Upload a video clip (`multipart/form-data`) for keyframe sampling, temporal jitter analysis, and lip-sync inspection.

**Form Data**:
- `file`: Video file (`.mp4`, `.mov`, `.webm`, max 150MB)

---

### `POST /verify/audio`
Upload an audio recording (`multipart/form-data`) for synthetic voice detection and speech claim verification.

**Form Data**:
- `file`: Audio file (`.wav`, `.mp3`, `.m4a`, max 50MB)

---

## 3. Jobs & Reports

### `GET /jobs/{job_id}`
Polls progress and current stage of an asynchronous verification job.

### `GET /reports/{report_id}`
Retrieves complete structured verification dossier.

### `GET /reports/{report_id}/pdf`
Downloads an official PDF document of the verification dossier.

### `DELETE /reports/{report_id}`
Permanently deletes the report and shreds any associated media files on disk.

### `GET /history`
Returns paginated list of previous reports (`?limit=25&offset=0`).

---

## 4. Admin Endpoints

### `POST /admin/login`
**Request Body**:
```json
{
  "username": "admin",
  "password": "capcheck123"
}
```
**Response**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "username": "admin",
  "role": "admin"
}
```

### `GET /admin/stats`
Returns system volume and completion metrics (Admin token required).

### `POST /admin/purge-old-files`
Triggers immediate cleanup of files older than 24 hours.
