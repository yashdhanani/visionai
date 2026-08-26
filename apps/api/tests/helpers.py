from __future__ import annotations

import io
from PIL import Image
import numpy as np


def generate_test_image(width=640, height=480, color=(100, 150, 200)) -> bytes:
    """Generate a simple test image and return JPEG bytes."""
    img = Image.fromarray(np.full((height, width, 3), color, dtype=np.uint8), "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def generate_synthetic_image_with_boxes(width=640, height=480) -> bytes:
    """Generate an image with rectangles that YOLO might detect as objects."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (40, 60, 80)

    # Draw shapes that look vaguely like objects
    import cv2
    cv2.rectangle(img, (50, 50), (200, 400), (180, 140, 100), -1)  # person-like
    cv2.circle(img, (350, 120), 40, (200, 200, 150), -1)  # ball-like
    cv2.rectangle(img, (400, 200), (600, 450), (150, 80, 40), -1)  # box-like
    cv2.ellipse(img, (320, 350), (80, 50), 0, 0, 360, (100, 200, 100), -1)

    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()


def generate_test_video(frames=30, width=640, height=480) -> bytes:
    """Generate a short synthetic video for testing."""
    import cv2
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        path = f.name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 30.0, (width, height))

    for i in range(frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (40, 60, 80)
        import cv2
        x = int(50 + i * 10)
        cv2.rectangle(frame, (x, 50), (x + 100, 200), (0, 255, 0), -1)
        writer.write(frame)

    writer.release()
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data