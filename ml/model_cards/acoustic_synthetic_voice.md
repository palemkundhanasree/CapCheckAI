# Model Card: Acoustic Dynamic Range & ZCR Synthetic Voice Detector

## Model Overview
- **Name**: Acoustic Dynamic Range & Zero-Crossing Rate Synthetic Voice Detector
- **Version**: 1.1.0
- **Type**: Acoustic Forensics & Spectral Signal Processing
- **Primary Use**: Detecting text-to-speech vocoder outputs, voice cloning, and synthetic speech synthesis.

## Methodology
Human biological speech features natural pitch glides, micro-tremors in vocal cord vibration, breath intake pauses, and dynamic amplitude fluctuations across phoneme boundaries. Text-to-speech vocoders (e.g., HiFi-GAN, WaveGlow, Diffusion Vocoders) typically compress the acoustic dynamic range and produce uncharacteristic zero-crossing distributions in sibilant and unvoiced consonants.

## Performance Metrics
- **Dataset Evaluated**: In-the-Wild Voice Cloning Benchmark
- **Accuracy**: 86.5%
- **Precision**: 85.0%
- **Recall**: 89.2%

## Limitations
1. **Low-Bitrate Telephone Codecs**: GSM and AMR phone audio encoders introduce heavy compression artifacts that can mimic vocoder characteristics.
2. **Heavy Background Noise / Reverb**: Strong background music or reverberation masks subtle spectral features.
