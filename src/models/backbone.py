"""Semantic-only ConvNeXt-Tiny baseline for M3."""

from __future__ import annotations

import timm
import torch
from torch import nn


MODEL_NAME = "convnext_tiny.fb_in22k_ft_in1k_384"


class SemanticConvNeXtTiny(nn.Module):
    def __init__(self, num_classes: int = 3, pretrained: bool = True) -> None:
        super().__init__()
        self.model = timm.create_model(MODEL_NAME, pretrained=pretrained, num_classes=num_classes)
        self.freeze_paper_oriented()

    def freeze_paper_oriented(self) -> None:
        for parameter in self.model.parameters():
            parameter.requires_grad = False
        for parameter in self.model.stages[3].parameters():
            parameter.requires_grad = True
        # timm ConvNeXt head contains global pooling, final norm, flatten/dropout, and fc.
        for parameter in self.model.head.parameters():
            parameter.requires_grad = True

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.model(images)

    def classifier_parameters(self):
        return self.model.head.fc.parameters()

    def backbone_parameters(self):
        classifier_ids = {id(parameter) for parameter in self.classifier_parameters()}
        return (parameter for parameter in self.parameters() if parameter.requires_grad and id(parameter) not in classifier_ids)

    def parameter_summary(self) -> dict[str, int]:
        total = sum(parameter.numel() for parameter in self.parameters())
        trainable = sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)
        return {"total": total, "trainable": trainable, "frozen": total - trainable}

    def assert_freeze_policy(self) -> None:
        assert all(not parameter.requires_grad for parameter in self.model.stem.parameters())
        for stage in self.model.stages[:3]:
            assert all(not parameter.requires_grad for parameter in stage.parameters())
        assert all(parameter.requires_grad for parameter in self.model.stages[3].parameters())
        assert all(parameter.requires_grad for parameter in self.model.head.parameters())
