"""Fixed-Sobel, pixel-only edge-forensics branch for M5."""
from __future__ import annotations
import torch
from torch import nn
from torch.nn import functional as F

class EdgeBranch(nn.Module):
    output_dim = 32
    def __init__(self, epsilon: float = 1e-6) -> None:
        super().__init__(); self.epsilon = epsilon
        self.register_buffer("sobel_x", torch.tensor([[-1.,0.,1.],[-2.,0.,2.],[-1.,0.,1.]]).view(1,1,3,3))
        self.register_buffer("sobel_y", torch.tensor([[-1.,-2.,-1.],[0.,0.,0.],[1.,2.,1.]]).view(1,1,3,3))
        self.features = nn.Sequential(nn.Conv2d(1,16,3,padding=1,bias=False),nn.BatchNorm2d(16),nn.ReLU(inplace=True),nn.Conv2d(16,32,3,padding=1,bias=False),nn.BatchNorm2d(32),nn.ReLU(inplace=True))
        self.pool = nn.AdaptiveAvgPool2d(1); self.output = nn.Linear(32,32)
    def edge_maps(self, images: torch.Tensor):
        gray = 0.2989*images[:,0:1] + 0.5870*images[:,1:2] + 0.1140*images[:,2:3]
        gx, gy = F.conv2d(gray,self.sobel_x,padding=1), F.conv2d(gray,self.sobel_y,padding=1)
        return gray, torch.sqrt(gx.square()+gy.square()+self.epsilon)
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        _, magnitude = self.edge_maps(images); return self.output(self.pool(self.features(magnitude)).flatten(1))
