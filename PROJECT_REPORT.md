# Project Report

## Title

**Low-Cost 3D Surface Reconstruction Using Photometric Stereo**

## Abstract

This project presents a lightweight computer vision system for reconstructing the surface characteristics of a small object using four images captured under different lighting directions. The method is based on photometric stereo, which estimates surface normals and albedo from illumination changes while keeping the camera viewpoint fixed. The estimated normals are then integrated to obtain an approximate depth map. The project uses only classical image processing and linear algebra, making it suitable for low-resource academic environments. It avoids deep learning, large datasets, and GPU dependency while still producing visually meaningful outputs such as object mask, albedo image, normal map, depth map, and relit preview. The work is directly aligned with the Computer Vision syllabus topics of image formation, segmentation, reflectance, albedo estimation, and Shape From X.

## 1. Introduction

Computer vision aims to extract meaningful information from images and videos. Many practical systems focus on recognition, detection, and tracking, but another important branch of computer vision studies how physical properties of surfaces can be recovered from image observations. One such approach is photometric stereo, where the same object is observed multiple times under varying illumination. By analyzing changes in intensity, it is possible to estimate the orientation of the surface at each pixel.

This project explores photometric stereo as a low-cost and syllabus-relevant application of computer vision. The project was chosen because it is more original than common student submissions and can be implemented with minimal computational resources. A mobile phone camera, controlled lighting, and four images are sufficient to generate an approximate 3D-like reconstruction of an object.

## 2. Problem Statement

Most commonly submitted computer vision projects depend on popular application templates such as face recognition, attendance systems, general object detection, or video tracking. These projects are often repetitive and may rely on pretrained models or larger computational setups. The challenge addressed in this work is to design a project that is:

- strongly connected to the course syllabus
- technically meaningful
- visually impressive
- unique among student submissions
- feasible with low resource usage

The problem is therefore to reconstruct useful surface information from a small number of images without using deep learning or expensive hardware.

## 3. Objectives

- To build a computer vision project directly derived from the uploaded syllabus.
- To estimate the albedo and surface normal map of an object using photometric stereo.
- To recover an approximate depth map from the estimated normals.
- To keep the project lightweight in terms of computation, memory, and setup.
- To produce an interpretable output that is easy to demonstrate and explain.

## 4. Scope

The project focuses on small, mostly matte objects captured using a fixed camera. It is intended for educational demonstration rather than industrial-grade 3D scanning. The system assumes that the camera does not move between images and that illumination changes are the primary cause of appearance variation.

## 5. Syllabus Mapping

The selected topic maps directly to the Computer Vision syllabus as follows:

- **Module 1: Digital Image Formation and Low Level Processing**
  - image formation
  - filtering
  - intensity normalization
- **Module 3: Feature Extraction and Image Segmentation**
  - segmentation
  - edge and region related preprocessing
- **Module 5: Shape From X**
  - light at surfaces
  - reflectance behavior
  - albedo estimation
  - photometric stereo

This makes the project academically strong because it is clearly tied to core course concepts instead of using unrelated black-box tools.

## 6. Literature Background

Photometric stereo is a classical method used to recover surface orientation by observing an object under multiple light directions. Under Lambertian reflectance assumptions, the image intensity at a pixel depends on the dot product between the surface normal and the lighting direction, scaled by albedo. If enough images are captured under known illumination directions, the normal and albedo can be solved using linear algebra.

In this project, the method is simplified for low-cost implementation:

- only four input images are used
- approximate light directions are predefined
- grayscale processing is used to reduce complexity
- depth is recovered by integrating the normal field

Although simplified, the approach demonstrates the essential theory behind shape recovery from illumination.

## 7. Methodology

### 7.1 Input Acquisition

The same object is photographed four times:

- light from left
- light from right
- light from top
- light from bottom

The camera remains fixed across all captures. The object should be matte and placed on a simple background for better segmentation.

### 7.2 Preprocessing

Each input image is:

- read in grayscale
- blurred using Gaussian filtering to reduce noise
- normalized using percentile-based intensity scaling

This preprocessing improves the stability of later estimation stages.

### 7.3 Object Segmentation

The average image from all captures is used to generate a rough object mask. Otsu thresholding and morphological operations are applied to separate the object from the background. This step removes irrelevant background pixels and improves the quality of the estimated results.

### 7.4 Photometric Stereo Estimation

For each pixel, the observed intensities from the four images are stacked into a vector. Let:

- `I` be the intensity vector
- `L` be the lighting direction matrix
- `g` be the scaled normal vector

Then:

`I = Lg`

By solving this system using the pseudoinverse of the light matrix, the vector `g` is obtained. From `g`:

- albedo is computed as the magnitude of `g`
- surface normal is computed by normalizing `g`

### 7.5 Depth Recovery

The estimated normal map provides local surface orientation. The horizontal and vertical surface gradients are derived from the normal components. These gradients are integrated using an FFT-based method to recover an approximate depth surface.

### 7.6 Output Generation

The program saves:

- mean input visualization
- binary object mask
- albedo image
- normal map
- depth heatmap
- relit preview image
- numerical summary in JSON format

## 8. Algorithm

1. Capture four aligned images of the object under different light directions.
2. Load all images in grayscale.
3. Apply Gaussian smoothing and intensity normalization.
4. Build an object mask using thresholding and morphology.
5. Define or load the lighting direction matrix.
6. Solve the photometric stereo equation using matrix pseudoinverse.
7. Compute albedo and normal map.
8. Convert normals into surface gradients.
9. Integrate gradients to estimate depth.
10. Save and visualize the outputs.

## 9. Software and Hardware Requirements

### Software

- Python 3.10 or above
- NumPy
- OpenCV

### Hardware

- laptop or desktop with normal CPU
- mobile phone camera for capturing images
- basic torch or phone flashlight for directional illumination

No GPU or high-end hardware is required.

## 10. Implementation Details

The implementation is contained in [run_photometric_stereo.py](pocket_photometric_stereo/run_photometric_stereo.py). The program:

- automatically locates `left`, `right`, `top`, and `bottom` images
- supports optional resizing for faster execution
- allows custom light directions using [lights_example.json](pocket_photometric_stereo/lights_example.json)
- saves all outputs into the `output` folder

The design intentionally uses only standard scientific Python tools to keep installation simple.

## 11. Expected Results

After successful execution, the system is expected to produce:

- a clean foreground mask showing the target object
- an albedo image representing surface reflectance
- a color-coded normal map showing local surface orientation
- a depth map representing approximate object relief
- a relit preview that visually confirms surface reconstruction quality

The exact quality depends on capture quality, lighting direction consistency, object texture, and how matte the surface is.

## 12. Advantages of the Proposed Project

- unique topic selection compared to common class projects
- direct relevance to advanced syllabus topics
- low memory and computational cost
- no dataset collection or annotation burden
- no dependence on pretrained deep learning models
- easy to explain mathematically in viva
- visually strong outputs for demonstration

## 13. Limitations

- assumes roughly Lambertian or matte surfaces
- sensitive to specular highlights and shiny materials
- requires the object and camera to remain fixed
- depth is relative and approximate, not an exact metric 3D model
- segmentation quality can affect final reconstruction quality

## 14. Applications

- low-cost educational demonstrations
- small object surface inspection
- texture and relief analysis
- cultural artifact digitization
- introductory shape recovery experiments

## 15. Future Enhancements

- use more than four light directions for improved robustness
- include shadow handling and outlier rejection
- support color photometric stereo
- add interactive 3D visualization
- improve segmentation using adaptive object extraction
- extend to calibrated lighting setups for better depth accuracy

## 16. Conclusion

This project demonstrates that meaningful 3D surface information can be recovered using classical computer vision with very limited resources. By using photometric stereo, the system estimates albedo, normals, and depth from only four images captured under directional lighting. The result is a unique, syllabus-driven, low-cost project that balances theoretical depth, implementation feasibility, and presentation value. It is therefore a strong candidate for academic submission in a Computer Vision course.

## 17. References

1. Richard Szeliski, *Computer Vision: Algorithms and Applications*, Springer, 2011.
2. D. A. Forsyth and J. Ponce, *Computer Vision: A Modern Approach*, Pearson Education, 2003.
3. Richard Hartley and Andrew Zisserman, *Multiple View Geometry in Computer Vision*, Cambridge University Press, 2004.
4. Rafael C. Gonzalez and Richard E. Woods, *Digital Image Processing*, Addison-Wesley, 1992.
