"""
Utility functions for image processing and face mesh extraction.

Fixes in this version:
- Replaced use_column_width with use_container_width
- More robust face detection:
  * Auto-resize very small or very large images
  * Try multiple detection confidence levels
  * Support RGBA, grayscale, and BGR images
  * Better error messages with actionable tips
"""

import os
import io
import numpy as np
from typing import Optional, Tuple, List
from PIL import Image, ImageEnhance


# ── Image loading ──────────────────────────────────────────────────────────────

def image_obj_to_numpy(image_obj) -> np.ndarray:
    """
    Convert a Streamlit UploadedFile to an RGB numpy array.
    Handles RGBA, grayscale, palette mode, and orientation (EXIF).
    """
    image_obj.seek(0)
    pil_img = Image.open(image_obj)

    # Fix EXIF orientation
    try:
        from PIL import ImageOps
        pil_img = ImageOps.exif_transpose(pil_img)
    except Exception:
        pass

    # Convert any mode to RGB
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    return np.array(pil_img)


def preprocess_for_detection(image_np: np.ndarray) -> np.ndarray:
    """
    Preprocess image to maximise face detection success:
    - Resize if too small (upscale) or too large (downscale)
    - Slight contrast enhancement
    """
    pil = Image.fromarray(image_np)
    w, h = pil.size

    # Upscale very small images — MediaPipe struggles below 100px
    if min(w, h) < 120:
        scale = 120 / min(w, h)
        pil = pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Downscale very large images to speed up + avoid memory issues
    if max(w, h) > 1920:
        scale = 1920 / max(w, h)
        pil = pil.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Mild contrast boost helps with dark / washed-out photos
    pil = ImageEnhance.Contrast(pil).enhance(1.2)

    return np.array(pil)


# ── Face mesh extraction ───────────────────────────────────────────────────────

def extract_face_mesh_landmarks(image_np: np.ndarray) -> Optional[list]:
    """
    Extract and normalise MediaPipe Face Mesh landmarks.

    Strategy:
    1. Preprocess image (resize, contrast)
    2. Try detection at multiple confidence levels (0.3 → 0.1)
    3. Normalise: nose tip = origin, inter-ocular distance = 1.0

    Returns flat list [x0,y0,z0, ...] or None if no face found.
    """
    try:
        import mediapipe as mp

        mp_face_mesh = mp.solutions.face_mesh

        # Preprocess
        processed = preprocess_for_detection(image_np)

        # Try progressively lower confidence thresholds
        for confidence in [0.3, 0.2, 0.1]:
            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=confidence,
            ) as face_mesh:
                results = face_mesh.process(processed)

            if results.multi_face_landmarks:
                lm  = results.multi_face_landmarks[0].landmark
                pts = np.array([[l.x, l.y, l.z] for l in lm], dtype=np.float32)

                # Normalise: nose tip (landmark 4) → origin
                pts -= pts[4]

                # Normalise: inter-ocular distance → 1.0
                iod = np.linalg.norm(pts[33] - pts[263])
                if iod > 1e-6:
                    pts /= iod

                return pts.flatten().tolist()

        return None  # No face found at any confidence level

    except ImportError:
        # MediaPipe not installed
        return None
    except Exception:
        return None


def get_detection_tips() -> str:
    """Return user-friendly tips when face detection fails."""
    return (
        "**Tips for better detection:**\n"
        "- 📸 Use a clear, frontal face photo\n"
        "- 💡 Ensure good lighting (avoid shadows on face)\n"
        "- 🔍 Face should be clearly visible and not too small\n"
        "- 🚫 Avoid sunglasses, masks, or heavy obstructions\n"
        "- 📐 Keep the face roughly centred in the image\n"
        "- 🖼️ Minimum recommended resolution: 200×200 px"
    )


# ── Similarity scoring ─────────────────────────────────────────────────────────

def cosine_similarity(a: list, b: list) -> float:
    va    = np.array(a, dtype=np.float64)
    vb    = np.array(b, dtype=np.float64)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom < 1e-10:
        return 0.0
    return float(np.dot(va, vb) / denom)


def euclidean_distance(a: list, b: list) -> float:
    va   = np.array(a, dtype=np.float64)
    vb   = np.array(b, dtype=np.float64)
    diff = (va - vb).reshape(-1, 3)
    return float(np.mean(np.linalg.norm(diff, axis=1)))


def hybrid_similarity(mesh_a: list, mesh_b: list) -> float:
    """
    Combined score = 0.6 × cosine_similarity + 0.4 × euclidean_score
    Both components normalised to [0, 1].
    """
    if not mesh_a or not mesh_b:
        return 0.0
    n   = min(len(mesh_a), len(mesh_b))
    a, b = mesh_a[:n], mesh_b[:n]
    cos       = (cosine_similarity(a, b) + 1) / 2
    euc_score = 1.0 / (1.0 + euclidean_distance(a, b))
    return 0.6 * cos + 0.4 * euc_score


def find_best_match(
    query_mesh: list,
    candidates: List[dict],
    threshold: float = 0.60,
) -> Tuple[Optional[dict], float]:
    best_candidate = None
    best_score     = 0.0
    for c in candidates:
        score = hybrid_similarity(query_mesh, c["mesh"])
        if score > best_score:
            best_score     = score
            best_candidate = c
    if best_score >= threshold:
        return best_candidate, best_score
    return None, best_score


def confidence_label(score: float) -> str:
    if score >= 0.85: return "🟢 Very High"
    if score >= 0.70: return "🟡 High"
    if score >= 0.60: return "🟠 Moderate"
    return "🔴 Low (no match)"


# ── Image helpers ──────────────────────────────────────────────────────────────

def save_uploaded_image(uploaded_file, unique_id: str, folder: str = "./resources") -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{unique_id}.jpg")
    uploaded_file.seek(0)
    img = Image.open(uploaded_file).convert("RGB")
    img.save(path, "JPEG", quality=92)
    return path
