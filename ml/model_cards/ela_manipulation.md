# Model Card: Error Level Analysis (ELA) Splicing Detector

## Model Overview
- **Name**: Error Level Analysis (ELA) Splicing & Tampering Detector
- **Version**: 1.0.4
- **Type**: JPEG Quantization Error Forensics
- **Primary Use**: Localization of digital image splicing, copy-paste cloning, and Photoshop retouching.

## Methodology
When an image is saved in JPEG format, each $8\times 8$ pixel block undergoes Discrete Cosine Transformation (DCT) and is quantized using a specific quantization table. Re-saving an unedited image at 95% quality produces uniform residual differences across all blocks. When foreign elements or retouched patches are introduced, those regions exhibit significantly higher error levels compared to the rest of the image.

## Performance Metrics
- **Dataset Evaluated**: CASIA Image Tampering Evaluation Set
- **Accuracy**: 84.2%
- **Precision**: 82.5%
- **Recall**: 87.1%

## Limitations
1. **High-Contrast Edges**: Natural sharp edges (e.g. text against white background or high-contrast architectural silhouettes) naturally produce higher ELA residuals without being manipulated.
2. **Multiple Save Iterations**: An image saved dozens of times reaches quantization error equilibrium, reducing ELA contrast.
