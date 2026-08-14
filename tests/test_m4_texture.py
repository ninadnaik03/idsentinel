import tempfile
import unittest
from pathlib import Path

import torch
from torch import nn

from src.models.convnext_texture import ConvNeXtTexture
from src.models.texture_branch import TextureBranch
from src.training.metrics import classification_metrics


class M4TextureTests(unittest.TestCase):
    def test_texture_shape(self):
        output = TextureBranch()(torch.randn(2, 3, 384, 384))
        self.assertEqual(tuple(output.shape), (2, 64))

    def test_shapes_gradients_optimizer_and_checkpoint(self):
        model = ConvNeXtTexture(pretrained=False)
        model.assert_freeze_policy()
        model.train()
        images, targets = torch.randn(2, 3, 384, 384), torch.tensor([0, 2])
        logits, features = model(images, return_features=True)
        self.assertEqual(tuple(features["texture"].shape), (2, 64))
        self.assertEqual(tuple(features["semantic_projected"].shape), (2, 256))
        self.assertEqual(tuple(features["texture_projected"].shape), (2, 256))
        self.assertEqual(tuple(features["combined"].shape), (2, 256))
        self.assertEqual(tuple(logits.shape), (2, 3))
        optimizer = torch.optim.AdamW(model.optimizer_parameter_groups(), weight_decay=0.01)
        loss = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 1.1, 0.9]))(logits, targets)
        loss.backward()
        self.assertIsNotNone(model.branch_logits.grad)
        self.assertTrue(torch.all(model.branch_logits.grad.abs() > 0))
        optimizer.step()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            torch.save({"model": model.state_dict()}, path)
            clone = ConvNeXtTexture(pretrained=False)
            clone.load_state_dict(torch.load(path, weights_only=True)["model"])
        metrics = classification_metrics(targets.tolist(), logits.argmax(1).tolist())
        self.assertIn("macro_f1", metrics)


if __name__ == "__main__":
    unittest.main()
