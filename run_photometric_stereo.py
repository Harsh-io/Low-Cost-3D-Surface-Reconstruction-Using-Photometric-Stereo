import argparse
import json
from pathlib import Path

import cv2
import numpy as np


DEFAULT_LIGHTS = {
    "left": [1.0, 0.0, 1.0],
    "right": [-1.0, 0.0, 1.0],
    "top": [0.0, -1.0, 1.0],
    "bottom": [0.0, 1.0, 1.0],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Low-resource photometric stereo from 4 directional images."
    )
    parser.add_argument(
        "--input-dir",
        default="sample_input",
        help="Folder containing left/right/top/bottom images.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Folder where outputs will be saved.",
    )
    parser.add_argument(
        "--lights-file",
        default="",
        help="Optional JSON file mapping image names to 3D light directions.",
    )
    parser.add_argument(
        "--blur-kernel",
        type=int,
        default=5,
        help="Gaussian blur kernel size for denoising.",
    )
    parser.add_argument(
        "--resize-width",
        type=int,
        default=0,
        help="Optional resize width for faster processing. 0 keeps original size.",
    )
    return parser.parse_args()


def ensure_odd(value):
    value = max(1, int(value))
    return value if value % 2 == 1 else value + 1


def load_light_directions(lights_file):
    defaults = {
        key: normalize_vector(np.array(vec, dtype=np.float32))
        for key, vec in DEFAULT_LIGHTS.items()
    }
    if not lights_file:
        return defaults

    with open(lights_file, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    for key, vec in raw.items():
        normalized_key = key.lower()
        if normalized_key not in DEFAULT_LIGHTS:
            raise ValueError(
                f"Unsupported light name '{key}'. Use left, right, top, or bottom."
            )
        defaults[normalized_key] = normalize_vector(np.array(vec, dtype=np.float32))
    return defaults


def normalize_vector(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Light direction vector cannot be zero.")
    return vector / norm


def discover_images(input_dir):
    image_map = {}
    for key in DEFAULT_LIGHTS:
        for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
            candidate = input_dir / f"{key}{ext}"
            if candidate.exists():
                image_map[key] = candidate
                break
    missing = [key for key in DEFAULT_LIGHTS if key not in image_map]
    if missing:
        raise FileNotFoundError(
            "Missing required images: " + ", ".join(missing) + ". "
            "Expected files like left.jpg, right.jpg, top.jpg, bottom.jpg."
        )
    return image_map


def read_and_preprocess(image_path, blur_kernel, resize_width):
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    if resize_width > 0:
        scale = resize_width / image.shape[1]
        resize_height = max(1, int(round(image.shape[0] * scale)))
        image = cv2.resize(image, (resize_width, resize_height), interpolation=cv2.INTER_AREA)

    blur_kernel = ensure_odd(blur_kernel)
    image = cv2.GaussianBlur(image, (blur_kernel, blur_kernel), 0)
    image = image.astype(np.float32) / 255.0

    low, high = np.percentile(image, [1, 99])
    if high > low:
        image = np.clip((image - low) / (high - low), 0.0, 1.0)
    return image


def build_mask(images):
    stacked = np.stack(images, axis=0)
    mean_image = np.mean(stacked, axis=0)
    scaled = np.uint8(np.clip(mean_image * 255.0, 0, 255))
    _, mask = cv2.threshold(
        scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    white_ratio = np.mean(mask > 0)
    if white_ratio > 0.75:
        mask = cv2.bitwise_not(mask)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask.astype(bool)


def compute_photometric_stereo(image_map, light_map, blur_kernel, resize_width):
    ordered_names = ["left", "right", "top", "bottom"]
    ordered_images = [
        read_and_preprocess(image_map[name], blur_kernel, resize_width)
        for name in ordered_names
    ]

    heights = {img.shape[0] for img in ordered_images}
    widths = {img.shape[1] for img in ordered_images}
    if len(heights) != 1 or len(widths) != 1:
        raise ValueError("All images must share the same dimensions.")

    mask = build_mask(ordered_images)
    image_stack = np.stack(ordered_images, axis=0)
    light_matrix = np.stack([light_map[name] for name in ordered_names], axis=0)

    pseudo_inverse = np.linalg.pinv(light_matrix)
    pixel_vectors = image_stack.reshape(image_stack.shape[0], -1)
    g = pseudo_inverse @ pixel_vectors

    albedo = np.linalg.norm(g, axis=0)
    safe_albedo = np.where(albedo > 1e-6, albedo, 1.0)
    normals = g / safe_albedo
    normals[:, albedo <= 1e-6] = 0.0

    albedo_img = albedo.reshape(mask.shape)
    normals_img = normals.T.reshape(mask.shape[0], mask.shape[1], 3)

    albedo_img[~mask] = 0.0
    normals_img[~mask] = 0.0
    return ordered_images, mask, albedo_img, normals_img


def integrate_normals(normals, mask):
    nx = normals[:, :, 0]
    ny = normals[:, :, 1]
    nz = normals[:, :, 2]

    safe_nz = np.where(np.abs(nz) < 1e-6, 1e-6, nz)
    p = np.where(mask, -nx / safe_nz, 0.0)
    q = np.where(mask, -ny / safe_nz, 0.0)

    rows, cols = p.shape
    wx = np.fft.fftfreq(cols).reshape(1, cols) * 2.0 * np.pi
    wy = np.fft.fftfreq(rows).reshape(rows, 1) * 2.0 * np.pi

    p_fft = np.fft.fft2(p)
    q_fft = np.fft.fft2(q)
    denom = wx**2 + wy**2
    denom[0, 0] = 1.0

    depth_fft = (-1j * wx * p_fft - 1j * wy * q_fft) / denom
    depth_fft[0, 0] = 0.0
    depth = np.real(np.fft.ifft2(depth_fft))

    depth[~mask] = 0.0
    if np.any(mask):
        depth = depth - np.median(depth[mask])
    return depth


def normalize_for_save(image):
    if image.ndim == 2:
        finite = np.isfinite(image)
        if not np.any(finite):
            return np.zeros_like(image, dtype=np.uint8)
        valid = image[finite]
        low, high = np.percentile(valid, [1, 99])
        if high <= low:
            return np.uint8(np.clip(image, 0.0, 1.0) * 255.0)
        scaled = np.clip((image - low) / (high - low), 0.0, 1.0)
        return np.uint8(scaled * 255.0)

    scaled = np.clip((image + 1.0) * 0.5, 0.0, 1.0)
    return np.uint8(scaled * 255.0)


def save_outputs(output_dir, source_images, mask, albedo, normals, depth):
    output_dir.mkdir(parents=True, exist_ok=True)

    mean_input = np.mean(np.stack(source_images, axis=0), axis=0)
    cv2.imwrite(str(output_dir / "01_mean_input.png"), normalize_for_save(mean_input))
    cv2.imwrite(str(output_dir / "02_mask.png"), np.uint8(mask) * 255)
    cv2.imwrite(str(output_dir / "03_albedo.png"), normalize_for_save(albedo))

    normal_vis = normalize_for_save(normals)
    normal_vis[~mask] = 0
    cv2.imwrite(str(output_dir / "04_normal_map.png"), cv2.cvtColor(normal_vis, cv2.COLOR_RGB2BGR))

    depth_vis = normalize_for_save(depth)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_TURBO)
    depth_color[~mask] = 0
    cv2.imwrite(str(output_dir / "05_depth_map.png"), depth_color)

    shaded = render_lambertian(normals, albedo, mask, np.array([0.4, -0.3, 1.0], dtype=np.float32))
    cv2.imwrite(str(output_dir / "06_relit_preview.png"), np.uint8(np.clip(shaded, 0.0, 1.0) * 255.0))


def render_lambertian(normals, albedo, mask, light_direction):
    light_direction = normalize_vector(light_direction.astype(np.float32))
    intensity = np.clip(np.sum(normals * light_direction.reshape(1, 1, 3), axis=2), 0.0, 1.0)
    shaded = intensity * np.clip(albedo, 0.0, 1.0)
    shaded_rgb = np.dstack([shaded, shaded, shaded])
    shaded_rgb[~mask] = 0.0
    return shaded_rgb


def write_summary(output_dir, light_map, mask, albedo, depth):
    summary = {
        "lights": {key: [float(v) for v in vec] for key, vec in light_map.items()},
        "mask_coverage_percent": float(np.mean(mask) * 100.0),
        "mean_albedo": float(np.mean(albedo[mask])) if np.any(mask) else 0.0,
        "depth_min": float(np.min(depth[mask])) if np.any(mask) else 0.0,
        "depth_max": float(np.max(depth[mask])) if np.any(mask) else 0.0,
    }
    with open(output_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    light_map = load_light_directions(args.lights_file)
    image_map = discover_images(input_dir)

    source_images, mask, albedo, normals = compute_photometric_stereo(
        image_map=image_map,
        light_map=light_map,
        blur_kernel=args.blur_kernel,
        resize_width=args.resize_width,
    )
    depth = integrate_normals(normals, mask)
    save_outputs(output_dir, source_images, mask, albedo, normals, depth)
    write_summary(output_dir, light_map, mask, albedo, depth)

    print("Photometric stereo completed successfully.")
    print(f"Input directory : {input_dir.resolve()}")
    print(f"Output directory: {output_dir.resolve()}")
    print("Saved outputs:")
    print("  01_mean_input.png")
    print("  02_mask.png")
    print("  03_albedo.png")
    print("  04_normal_map.png")
    print("  05_depth_map.png")
    print("  06_relit_preview.png")
    print("  summary.json")


if __name__ == "__main__":
    main()
