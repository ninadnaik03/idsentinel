import unittest

import numpy as np

from src.preprocessing.portrait import (
    Detection,
    PortraitExtractor,
    best_detection,
    context_crop,
    context_geometry,
)


class StubDetector:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def detect(self, image):
        self.calls.append(image.copy())
        return self.outputs.pop(0) if self.outputs else []


class PortraitTests(unittest.TestCase):
    def test_threshold_is_inclusive(self):
        detection = Detection((1, 1, 3, 3), 0.7)
        self.assertEqual(best_detection([detection], 0.7), detection)
        self.assertIsNone(best_detection([Detection((1, 1, 3, 3), 0.6999)], 0.7))

    def test_fallback_ordering(self):
        original = np.full((30, 40, 3), 100, np.uint8)
        retina = StubDetector([[], [Detection((10, 8, 20, 18), 0.8)]])
        haar = StubDetector([[Detection((1, 1, 4, 4), 1.0)]])
        result = PortraitExtractor(retina, haar, haar_validator=lambda image, detection: True).extract(original)
        self.assertEqual(result.detector, "clahe_retinaface")
        self.assertEqual(len(retina.calls), 2)
        self.assertEqual(len(haar.calls), 0)

    def test_crop_geometry_and_padding(self):
        geometry = context_geometry((0, 0, 10, 10), (20, 30, 3), alpha=0.8)
        self.assertGreater(geometry[4], 0)
        self.assertGreater(geometry[5], 0)
        crop = context_crop(np.zeros((20, 30, 3), np.uint8), (0, 0, 10, 10))
        self.assertEqual(crop.shape, (384, 384, 3))

    def test_deterministic_output(self):
        image = np.arange(30 * 40 * 3, dtype=np.uint8).reshape(30, 40, 3)
        self.assertTrue(np.array_equal(context_crop(image, (10, 5, 20, 15)), context_crop(image, (10, 5, 20, 15))))

    def test_crop_uses_original_after_clahe_detection(self):
        original = np.zeros((30, 40, 3), np.uint8)
        original[5:25, 5:30] = (10, 20, 30)
        retina = StubDetector([[], [Detection((10, 8, 20, 18), 0.9)]])
        result = PortraitExtractor(retina, StubDetector([])).extract(original)
        expected = context_crop(original, (10, 8, 20, 18))
        self.assertTrue(np.array_equal(result.crop, expected))

    def test_template_is_last(self):
        result = PortraitExtractor(StubDetector([[], []]), StubDetector([[]])).extract(np.zeros((50, 80, 3), np.uint8))
        self.assertEqual(result.detector, "template")

    def test_implausible_haar_continues_to_template(self):
        original = np.zeros((100, 100, 3), np.uint8)
        haar = StubDetector([[Detection((1, 1, 10, 10), 1.0)]])
        result = PortraitExtractor(StubDetector([[], []]), haar, haar_validator=lambda image, detection: False).extract(original)
        self.assertEqual(result.detector, "template")

    def test_plausible_haar_is_retained(self):
        original = np.zeros((100, 100, 3), np.uint8)
        haar = StubDetector([[Detection((30, 30, 60, 65), 1.0)]])
        result = PortraitExtractor(StubDetector([[], []]), haar, haar_validator=lambda image, detection: True).extract(original)
        self.assertEqual(result.detector, "haar")


if __name__ == "__main__":
    unittest.main()
