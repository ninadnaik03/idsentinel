"""Paper-derived multi-fallback portrait extraction.

Crop interpretation: for a detected face box of width ``w`` and height ``h``,
alpha=0.8 adds ``0.8*w`` horizontally and ``0.8*h`` vertically on every side.
The resulting rectangle is expanded to a square, clipped to valid source pixels,
and missing border context is reflect-padded before resizing to 384x384.
Detection may use CLAHE pixels, but ``context_crop`` always receives the original.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence

import cv2
import numpy as np
import onnxruntime as ort


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Detection:
    bbox: BBox
    confidence: float


@dataclass(frozen=True)
class ExtractionResult:
    bbox: BBox | None
    detector: str
    confidence: float | None
    success: bool
    crop: np.ndarray | None
    padding_applied: bool


class Detector(Protocol):
    def detect(self, image: np.ndarray) -> Sequence[Detection]: ...


def _priors(height: int, width: int) -> np.ndarray:
    min_sizes = ((16, 32), (64, 128), (256, 512))
    steps = (8, 16, 32)
    anchors: list[list[float]] = []
    for sizes, step in zip(min_sizes, steps, strict=True):
        for row in range(math.ceil(height / step)):
            for col in range(math.ceil(width / step)):
                for size in sizes:
                    anchors.append([(col + 0.5) * step / width, (row + 0.5) * step / height, size / width, size / height])
    return np.asarray(anchors, dtype=np.float32)


def _decode_boxes(loc: np.ndarray, priors: np.ndarray) -> np.ndarray:
    centers = priors[:, :2] + loc[:, :2] * 0.1 * priors[:, 2:]
    sizes = priors[:, 2:] * np.exp(loc[:, 2:] * 0.2)
    return np.concatenate((centers - sizes / 2, centers + sizes / 2), axis=1)


def _nms(boxes: np.ndarray, scores: np.ndarray, threshold: float = 0.4) -> list[int]:
    if not len(boxes):
        return []
    x1, y1, x2, y2 = boxes.T
    areas = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size:
        index = int(order[0])
        keep.append(index)
        xx1 = np.maximum(x1[index], x1[order[1:]])
        yy1 = np.maximum(y1[index], y1[order[1:]])
        xx2 = np.minimum(x2[index], x2[order[1:]])
        yy2 = np.minimum(y2[index], y2[order[1:]])
        intersection = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        union = areas[index] + areas[order[1:]] - intersection
        overlap = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
        order = order[np.concatenate(([False], overlap <= threshold))]
    return keep


class RetinaFaceONNX:
    """CPU-oriented MobileNet-0.25 RetinaFace ONNX detector."""

    def __init__(self, model_path: Path, candidate_threshold: float = 0.02) -> None:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model_path), options, providers=["CPUExecutionProvider"])
        self.candidate_threshold = candidate_threshold

    def detect(self, image: np.ndarray) -> Sequence[Detection]:
        height, width = image.shape[:2]
        scale = min(1.0, 1280.0 / max(height, width))
        working = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1 else image
        wh, ww = working.shape[:2]
        tensor = working.astype(np.float32) - np.asarray((104, 117, 123), dtype=np.float32)
        tensor = tensor.transpose(2, 0, 1)[None]
        loc, conf, _ = self.session.run(None, {"input": tensor})
        priors = _priors(wh, ww)
        boxes = _decode_boxes(loc[0], priors)
        boxes *= np.asarray((ww, wh, ww, wh), dtype=np.float32)
        scores = conf[0, :, 1]
        mask = scores >= self.candidate_threshold
        boxes, scores = boxes[mask], scores[mask]
        order = scores.argsort()[::-1][:5000]
        boxes, scores = boxes[order], scores[order]
        keep = _nms(boxes, scores)
        results = []
        for index in keep[:100]:
            x1, y1, x2, y2 = boxes[index] / scale
            results.append(Detection((float(x1), float(y1), float(x2), float(y2)), float(scores[index])))
        return results


class HaarDetector:
    def __init__(self) -> None:
        cascade = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.model = cv2.CascadeClassifier(str(cascade))

    def detect(self, image: np.ndarray) -> Sequence[Detection]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        boxes = self.model.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(24, 24))
        return [Detection((float(x), float(y), float(x + w), float(y + h)), 1.0) for x, y, w, h in boxes]


class HaarPlausibility:
    """Deterministic rejection rule for obvious Haar false positives."""

    def __init__(self) -> None:
        cascade = Path(cv2.data.haarcascades) / "haarcascade_eye.xml"
        self.eyes = cv2.CascadeClassifier(str(cascade))

    def __call__(self, image: np.ndarray, detection: Detection) -> bool:
        height, width = image.shape[:2]
        x1, y1, x2, y2 = detection.bbox
        x1i, y1i = max(0, math.floor(x1)), max(0, math.floor(y1))
        x2i, y2i = min(width, math.ceil(x2)), min(height, math.ceil(y2))
        bw, bh = x2i - x1i, y2i - y1i
        if bw < 24 or bh < 24:
            return False
        aspect = bw / bh
        area_ratio = bw * bh / (width * height)
        cx, cy = (x1i + x2i) / (2 * width), (y1i + y2i) / (2 * height)
        if not (0.65 <= aspect <= 1.55 and 0.0005 <= area_ratio <= 0.12 and 0.02 <= cx <= 0.98 and 0.02 <= cy <= 0.98):
            return False
        gray = cv2.cvtColor(image[y1i:y2i, x1i:x2i], cv2.COLOR_BGR2GRAY)
        if gray.size == 0 or float(gray.std()) < 10.0:
            return False
        upper = gray[: max(1, round(0.75 * gray.shape[0]))]
        eyes = self.eyes.detectMultiScale(upper, scaleFactor=1.1, minNeighbors=3, minSize=(6, 6))
        return len(eyes) >= 1


def clahe_image(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    light, a, b = cv2.split(lab)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(light)
    return cv2.cvtColor(cv2.merge((enhanced, a, b)), cv2.COLOR_LAB2BGR)


def best_detection(detections: Sequence[Detection], threshold: float) -> Detection | None:
    eligible = [item for item in detections if item.confidence >= threshold]
    if not eligible:
        return None
    return max(eligible, key=lambda item: ((item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]), item.confidence))


def template_bbox(image: np.ndarray, fractions: BBox = (0.18, 0.28, 0.42, 0.72)) -> BBox:
    height, width = image.shape[:2]
    x1, y1, x2, y2 = fractions
    return x1 * width, y1 * height, x2 * width, y2 * height


def context_geometry(bbox: BBox, image_shape: tuple[int, ...], alpha: float = 0.8) -> tuple[int, int, int, int, int, int, int, int]:
    height, width = image_shape[:2]
    x1, y1, x2, y2 = bbox
    bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
    px1, py1, px2, py2 = x1 - alpha * bw, y1 - alpha * bh, x2 + alpha * bw, y2 + alpha * bh
    side = max(px2 - px1, py2 - py1)
    cx, cy = (px1 + px2) / 2, (py1 + py2) / 2
    rx1, ry1, rx2, ry2 = math.floor(cx - side / 2), math.floor(cy - side / 2), math.ceil(cx + side / 2), math.ceil(cy + side / 2)
    left, top = max(0, -rx1), max(0, -ry1)
    right, bottom = max(0, rx2 - width), max(0, ry2 - height)
    return max(0, rx1), max(0, ry1), min(width, rx2), min(height, ry2), left, top, right, bottom


def context_crop(original: np.ndarray, bbox: BBox, alpha: float = 0.8, output_size: int = 384) -> np.ndarray:
    x1, y1, x2, y2, left, top, right, bottom = context_geometry(bbox, original.shape, alpha)
    crop = original[y1:y2, x1:x2].copy()
    if any((left, top, right, bottom)):
        mode = cv2.BORDER_REFLECT_101 if min(crop.shape[:2]) > 1 else cv2.BORDER_REPLICATE
        crop = cv2.copyMakeBorder(crop, top, bottom, left, right, mode)
    return cv2.resize(crop, (output_size, output_size), interpolation=cv2.INTER_AREA)


class PortraitExtractor:
    def __init__(self, retinaface: Detector, haar: Detector, threshold: float = 0.7, alpha: float = 0.8, template_fractions: BBox = (0.18, 0.28, 0.42, 0.72), haar_validator: Callable[[np.ndarray, Detection], bool] | None = None) -> None:
        self.retinaface, self.haar = retinaface, haar
        self.threshold, self.alpha, self.template_fractions = threshold, alpha, template_fractions
        self.haar_validator = haar_validator or HaarPlausibility()

    def extract(self, original: np.ndarray) -> ExtractionResult:
        detection = best_detection(self.retinaface.detect(original), self.threshold)
        detector = "retinaface"
        if detection is None:
            detection = best_detection(self.retinaface.detect(clahe_image(original)), self.threshold)
            detector = "clahe_retinaface"
        if detection is None:
            detection = best_detection(self.haar.detect(original), 0.0)
            detector = "haar"
            if detection is not None and not self.haar_validator(original, detection):
                detection = None
        if detection is None:
            bbox = template_bbox(original, self.template_fractions)
            detection = Detection(bbox, 0.0)
            detector = "template"
        geometry = context_geometry(detection.bbox, original.shape, self.alpha)
        crop = context_crop(original, detection.bbox, self.alpha)
        return ExtractionResult(detection.bbox, detector, detection.confidence, True, crop, any(geometry[4:]))
