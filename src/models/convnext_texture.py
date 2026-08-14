"""M4 ConvNeXt-Tiny plus texture model; no edge branch."""

from __future__ import annotations

import timm
import torch
from torch import nn

from .backbone import MODEL_NAME
from .texture_branch import TextureBranch


class ConvNeXtTexture(nn.Module):
    def __init__(self, num_classes: int = 3, projection_dim: int = 256, pretrained: bool = True) -> None:
        super().__init__()
        self.semantic = timm.create_model(MODEL_NAME, pretrained=pretrained, num_classes=0)
        self.texture = TextureBranch()
        self.semantic_projection = nn.Linear(self.semantic.num_features, projection_dim)
        self.texture_projection = nn.Linear(self.texture.output_dim, projection_dim)
        self.branch_logits = nn.Parameter(torch.zeros(2))
        self.classifier = nn.Sequential(
            nn.Linear(projection_dim, 512), nn.BatchNorm1d(512), nn.ReLU(inplace=True),
            nn.Linear(512, 256), nn.BatchNorm1d(256), nn.ReLU(inplace=True),
            nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(inplace=True),
            nn.Linear(128, num_classes),
        )
        self.freeze_paper_oriented()

    def freeze_paper_oriented(self) -> None:
        for parameter in self.semantic.parameters():
            parameter.requires_grad = False
        for parameter in self.semantic.stages[3].parameters():
            parameter.requires_grad = True
        # With num_classes=0 the head retains pooling and final norm but has an identity fc.
        for parameter in self.semantic.head.parameters():
            parameter.requires_grad = True

    def forward(self, images: torch.Tensor, return_features: bool = False):
        semantic = self.semantic.forward_head(self.semantic.forward_features(images), pre_logits=True)
        texture = self.texture(images)
        semantic_projected = self.semantic_projection(semantic)
        texture_projected = self.texture_projection(texture)
        weights = self.branch_logits.softmax(dim=0)
        combined = weights[0] * semantic_projected + weights[1] * texture_projected
        logits = self.classifier(combined)
        if not return_features:
            return logits
        return logits, {
            "semantic": semantic,
            "texture": texture,
            "semantic_projected": semantic_projected,
            "texture_projected": texture_projected,
            "combined": combined,
            "branch_weights": weights,
        }

    def optimizer_parameter_groups(self) -> list[dict]:
        return [
            {"params": [p for p in self.semantic.parameters() if p.requires_grad], "lr": 5e-7, "name": "trainable_backbone"},
            {"params": list(self.texture.parameters()), "lr": 1e-5, "name": "texture_branch"},
            {"params": list(self.semantic_projection.parameters()) + list(self.texture_projection.parameters()), "lr": 1e-5, "name": "projections"},
            {"params": [self.branch_logits], "lr": 1e-4, "name": "branch_weights"},
            {"params": list(self.classifier.parameters()), "lr": 5e-6, "name": "classifier"},
        ]

    def parameter_summary(self) -> dict[str, object]:
        components = {
            "semantic": sum(p.numel() for p in self.semantic.parameters()),
            "texture": sum(p.numel() for p in self.texture.parameters()),
            "projections": sum(p.numel() for m in (self.semantic_projection, self.texture_projection) for p in m.parameters()),
            "branch_weights": self.branch_logits.numel(),
            "classifier": sum(p.numel() for p in self.classifier.parameters()),
        }
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable, "frozen": total - trainable, "components": components}

    def assert_freeze_policy(self) -> None:
        assert all(not p.requires_grad for p in self.semantic.stem.parameters())
        assert all(not p.requires_grad for stage in self.semantic.stages[:3] for p in stage.parameters())
        assert all(p.requires_grad for p in self.semantic.stages[3].parameters())
        assert all(p.requires_grad for p in self.semantic.head.parameters())
