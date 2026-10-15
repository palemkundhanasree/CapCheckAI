# CapCheck AI — Data Retention & Privacy Policy

## 1. Core Principles
CapCheck AI was designed with privacy-by-default architecture:
- **Ephemeral Processing**: Media uploads are treated as temporary inputs for verification.
- **Immediate User Deletion**: Users have the unrestricted right to delete their dossiers, triggering atomic file unlinking.
- **No Third-Party AI Training**: Uploaded media is never transmitted to external commercial model vendors for model training or profiling.
- **SSRF Defense**: The crawler is prevented from fetching internal network endpoints or local loopback interfaces.

## 2. Retention Schedule
- **Temporary Uploads (`storage/uploads/`)**: Retained for a maximum of 48 hours to enable dossier generation, then automatically purged by the background cleaner.
- **Generated Reports (`storage/reports/`)**: Persisted in SQLite until explicitly deleted by the user or purged by an administrator.
- **Temporary Frames (`storage/temp/`)**: Purged automatically upon job completion.

## 3. Network Fetching Security
When crawling news URLs:
1. Only `http://` and `https://` schemes are permitted.
2. Hostnames undergo recursive DNS resolution.
3. Target IP addresses matching private (RFC 1918), loopback (`127.0.0.0/8`), or link-local (`169.254.0.0/16`) ranges are blocked immediately with an HTTP 403 Forbidden error.
4. Response bodies are strictly capped at 5MB to prevent decompression bombs.
