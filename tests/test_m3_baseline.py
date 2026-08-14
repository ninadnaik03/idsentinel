import unittest
from pathlib import Path

from src.data.baseline import CLASS_NAMES, load_and_validate_manifest, training_class_weights
from src.training.metrics import classification_metrics
from src.models.backbone import SemanticConvNeXtTiny


ROOT = Path(__file__).resolve().parents[1]


class M3BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.audit = load_and_validate_manifest(ROOT / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl")

    def test_frozen_manifest_invariants(self):
        self.assertEqual(len(self.records), 300)
        self.assertEqual(len(self.audit["manifest_sha256"]), 64)

    def test_class_weights_use_train_counts(self):
        weights = training_class_weights(self.records)
        self.assertAlmostEqual(weights[0], 214 / (3 * 71))
        self.assertAlmostEqual(weights[1], 214 / (3 * 71))
        self.assertAlmostEqual(weights[2], 214 / (3 * 72))

    def test_metrics(self):
        metrics = classification_metrics([0, 1, 2], [0, 2, 2])
        self.assertAlmostEqual(metrics["accuracy"], 2 / 3)
        self.assertEqual(metrics["confusion_matrix"], [[1, 0, 0], [0, 0, 1], [0, 0, 1]])

    def test_class_mapping_order(self):
        self.assertEqual(CLASS_NAMES, ("BONA_FIDE", "PRINT", "SCREEN"))

    def test_freeze_policy_and_logits(self):
        model = SemanticConvNeXtTiny(pretrained=False)
        model.assert_freeze_policy()
        summary = model.parameter_summary()
        self.assertEqual(summary["total"], summary["trainable"] + summary["frozen"])
        self.assertEqual(model.model.head.fc.out_features, 3)


if __name__ == "__main__":
    unittest.main()
