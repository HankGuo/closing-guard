import cv2
import numpy as np

from app import cv


def jpg(image: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", image)
    assert ok
    return buf.tobytes()


def test_quality_rejects_dark_blurry():
    image = np.zeros((320, 320, 3), dtype=np.uint8)
    result = cv.quality(jpg(image))
    assert result["ok"] is False
    assert result["reason"]


def test_dominant_angle_horizontal_line():
    image = np.full((400, 400, 3), 200, dtype=np.uint8)
    cv2.line(image, (60, 200), (340, 200), (0, 0, 0), 5)
    result = cv.dominant_angle(jpg(image))
    assert result["ok"] is True
    assert result["angle"] is not None
    assert min(abs(result["angle"]), 180 - abs(result["angle"])) < 8


def test_angle_delta_wraps():
    assert cv.angle_delta(2, 178) == 4
    assert cv.angle_delta(10, 90) == 80
    assert cv.angle_delta(None, 10) is None


def test_flame_check_detects_blue_flame():
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(image, (150, 150), 40, (255, 0, 0), -1)  # BGR blue
    result = cv.flame_check(jpg(image))
    assert result["suspected"] is True
    assert result["ratio"] > 0.004


def test_flame_check_plain_wall():
    image = np.full((300, 300, 3), 140, dtype=np.uint8)
    result = cv.flame_check(jpg(image))
    assert result["suspected"] is False
