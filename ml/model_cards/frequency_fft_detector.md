# Model Card: 2D-FFT Spatial Frequency Diffusion Detector

## Model Overview
- **Name**: 2D-FFT Spatial Frequency Diffusion Detector
- **Version**: 1.2.0
- **Type**: Spatial Frequency Forensics (Fast Fourier Transform)
- **Primary Use**: Identification of latent diffusion generative artifacts and checkerboard patterns in digital images.

## Methodology
Generative adversarial networks (GANs) and latent diffusion models (e.g., Stable Diffusion, Midjourney, DALL-E) utilize transposed convolutions and neural upsampling layers that imprint periodic, grid-like frequency artifacts into the generated image. This detector applies a 2-Dimensional Fast Fourier Transform, converts the complex spectrum to logarithmic magnitude, and measures the ratio of high-frequency energy decay versus expected natural optical decay.

## Performance Metrics
- **Dataset Evaluated**: Synthetic-Bench 2024 (10,000 samples)
- **Accuracy**: 88.4%
- **Precision**: 86.2%
- **Recall**: 91.0%
- **F1 Score**: 0.885

## Limitations and Failure Modes
1. **Aggressive Social Media Compression**: Platforms like Twitter/X and WhatsApp aggressively recompress uploaded images with lossy JPEG compression, which can attenuate subtle high-frequency spectral markers.
2. **Heavy Digital Noise / Film Grain**: Analog photographs with high ISO grain or artificial film grain filters may elevate high-frequency energy, occasionally triggering false positives if not cross-referenced with sensor noise PRNU.
