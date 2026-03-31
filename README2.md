# Pocket Photometric Stereo

## Project title

**Low-Cost 3D Surface Reconstruction Using Photometric Stereo**

## What this project does

This project reconstructs the surface shape of a small object using only:

- 1 phone camera
- 4 images
- 4 different light directions
- CPU-only classical computer vision

The program estimates:

- object mask
- albedo image
- normal map
- depth map
- relit preview

## Why this project is unique

Most students choose common topics like:

- face recognition
- object detection
- optical flow
- tracking

This project is different because it is based on **Shape From X / Photometric Stereo**, which is directly present in the syllabus but usually not selected by many students.

## Syllabus mapping

- **Module 1**: image formation, filtering, histogram/intensity normalization
- **Module 3**: segmentation, edge/region extraction
- **Module 5**: light at surfaces, albedo estimation, photometric stereo, shape from light

## Folder structure

```text
pocket_photometric_stereo/
|-- run_photometric_stereo.py
|-- requirements.txt
|-- lights_example.json
|-- README.md
|-- sample_input/
|   |-- left.jpg
|   |-- right.jpg
|   |-- top.jpg
|   `-- bottom.jpg
`-- output/
```

## How to capture input images

1. Place a small matte object on a plain background.
2. Keep the camera fixed.
3. Turn off moving background light as much as possible.
4. Capture 4 photos:
   - `left.jpg` with light from left
   - `right.jpg` with light from right
   - `top.jpg` with light from top
   - `bottom.jpg` with light from bottom
5. Make sure the object does not move between photos.

## Best objects

- coin
- leaf
- clay model
- carved eraser
- embossed paper
- small textured toy

Avoid:

- glass
- mirrors
- very shiny metal
- transparent objects

## Setup

Install Python 3.10+ and then:

```bash
pip install -r requirements.txt
```

## Run

```bash
python run_photometric_stereo.py --input-dir sample_input --output-dir output
```

Optional faster run:

```bash
python run_photometric_stereo.py --input-dir sample_input --output-dir output --resize-width 640
```

Optional custom light directions:

```bash
python run_photometric_stereo.py --input-dir sample_input --output-dir output --lights-file lights_example.json
```

## Output files

- `01_mean_input.png`: average of the input images
- `02_mask.png`: segmented object
- `03_albedo.png`: estimated reflectance
- `04_normal_map.png`: surface normal visualization
- `05_depth_map.png`: approximate depth reconstruction
- `06_relit_preview.png`: synthetic shading preview
- `summary.json`: basic numerical summary

## Method summary

1. Load 4 grayscale images.
2. Denoise and normalize intensity.
3. Build object mask using Otsu thresholding.
4. Use known light directions and solve the photometric stereo equation:

   `I = L * (albedo * normal)`

5. Estimate albedo and per-pixel surface normal.
6. Integrate the normal field using an FFT-based method to recover depth.
7. Save all results.

## Advantages

- low memory usage
- no training needed
- no GPU required
- zero dataset cost
- strong syllabus relevance
- visually impressive output

## Limitations

- works best for matte objects
- needs fixed camera position
- sensitive to shadows if lighting is too harsh
- depth is approximate, not true metric 3D scanning

##  explanation

> Instead of learning from a huge dataset, this project uses physics-based computer vision. I capture the same object under multiple lighting directions, estimate how light interacts with the surface, recover surface normals and albedo, and then integrate those normals to obtain an approximate depth map. This makes the project lightweight, unique, and directly connected to the Shape From X topics in the syllabus.
