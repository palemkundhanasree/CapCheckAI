# CapCheck AI — Model Evaluation & Limitations

## 1. Overview
Automated media forensics and fact verification models produce probabilistic estimates rather than definitive proof. This document describes the calibration, benchmarks, error bounds, and limitations of each forensic detector.

## 2. Evaluation Benchmarks

| Detector | Benchmark Dataset | Accuracy | Precision | Recall | F1 Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2D FFT Diffusion Detector** | DiffusionForensics-Bench (10k images) | 88.4% | 86.2% | 91.0% | 0.885 |
| **JPEG ELA Splicing Detector** | CASIA Tampering Evaluation Set | 84.2% | 82.5% | 87.1% | 0.847 |
| **Acoustic Vocoder ZCR Detector** | In-the-Wild Voice Clone Benchmark | 86.5% | 85.0% | 89.2% | 0.870 |
| **Temporal Video Jitter Analyzer** | FaceForensics++ (Sampled Set) | 82.1% | 79.4% | 85.6% | 0.824 |

## 3. False Positives and False Negatives

### False Positives
- **High-contrast natural edges**: Sharp boundaries (e.g. dark text against white billboards or crisp architectural silhouettes) naturally produce higher JPEG quantization errors without digital tampering.
- **Aggressive film grain / Analog cameras**: High ISO photographs possess pronounced grain that can elevate high-frequency FFT power spectrum metrics.
- **Voice acting & compressed phone codecs**: Low-bitrate cellular audio codecs (AMR / GSM) flatten dynamic range, occasionally mimicking vocoder characteristics.

### False Negatives
- **Heavy lossy re-encoding**: Repeated transcoding (e.g. video sent via WhatsApp, recorded from a screen, or compressed multiple times) blurs high-frequency diffusion artifacts.
- **Low-resolution images (< 256x256)**: Insufficient pixel grid dimensions prevent reliable 2D FFT spectral decomposition.

## 4. Confidence Score Calculation
The confidence rating reported in each dossier is a composite metric combining:
1. **Evidence Source Credibility** (Weighted 45%): Based on known registry reputation and IFCN accreditation.
2. **Stance Consensus Ratio** (Weighted 35%): Measures agreement percentage across corroborating vs. contradicting sources.
3. **Detector Extremity** (Weighted 20%): Measures statistical distance from the ambiguous 50% midpoint.
