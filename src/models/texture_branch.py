"""Pixel-only lightweight texture-forensics branch for M4."""

from __future__ import annotations

import torch
from torch import nn


class TextureBranch(nn.Module):
    """Map an RGB crop to a 64-D low-level texture representation."""

    output_dim = 64

    def __init__(self) -> None:
        super().__init__()
        self.pool32 = nn.AdaptiveAvgPool2d((32, 32))
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.global_pool = nn.AdaptiveAvgPool2d(1)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.global_pool(self.features(self.pool32(images))).flatten(1)
