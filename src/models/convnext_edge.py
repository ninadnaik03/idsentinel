"""M5 ConvNeXt-Tiny plus fixed-Sobel edge model; no texture branch."""
from __future__ import annotations
import timm, torch
from torch import nn
from .backbone import MODEL_NAME
from .edge_branch import EdgeBranch

class ConvNeXtEdge(nn.Module):
    def __init__(self,num_classes=3,projection_dim=256,pretrained=True):
        super().__init__(); self.semantic=timm.create_model(MODEL_NAME,pretrained=pretrained,num_classes=0); self.edge=EdgeBranch()
        self.semantic_projection=nn.Linear(self.semantic.num_features,projection_dim); self.edge_projection=nn.Linear(32,projection_dim); self.branch_logits=nn.Parameter(torch.zeros(2))
        self.classifier=nn.Sequential(nn.Linear(256,512),nn.BatchNorm1d(512),nn.ReLU(inplace=True),nn.Linear(512,256),nn.BatchNorm1d(256),nn.ReLU(inplace=True),nn.Linear(256,128),nn.BatchNorm1d(128),nn.ReLU(inplace=True),nn.Linear(128,num_classes)); self.freeze_paper_oriented()
    def freeze_paper_oriented(self):
        for p in self.semantic.parameters(): p.requires_grad=False
        for p in self.semantic.stages[3].parameters(): p.requires_grad=True
        for p in self.semantic.head.parameters(): p.requires_grad=True
    def forward(self,images,return_features=False):
        semantic=self.semantic.forward_head(self.semantic.forward_features(images),pre_logits=True); edge=self.edge(images); sp=self.semantic_projection(semantic); ep=self.edge_projection(edge); weights=self.branch_logits.softmax(0); combined=weights[0]*sp+weights[1]*ep; logits=self.classifier(combined)
        return (logits,{"semantic":semantic,"edge":edge,"semantic_projected":sp,"edge_projected":ep,"combined":combined,"branch_weights":weights}) if return_features else logits
    def optimizer_parameter_groups(self):
        return [{"params":[p for p in self.semantic.parameters() if p.requires_grad],"lr":5e-7,"name":"trainable_backbone"},{"params":list(self.edge.parameters()),"lr":1e-5,"name":"edge_branch"},{"params":list(self.semantic_projection.parameters())+list(self.edge_projection.parameters()),"lr":1e-5,"name":"projections"},{"params":[self.branch_logits],"lr":1e-4,"name":"branch_weights"},{"params":list(self.classifier.parameters()),"lr":5e-6,"name":"classifier"}]
    def parameter_summary(self):
        components={"semantic":sum(p.numel() for p in self.semantic.parameters()),"edge":sum(p.numel() for p in self.edge.parameters()),"projections":sum(p.numel() for m in (self.semantic_projection,self.edge_projection) for p in m.parameters()),"branch_weights":2,"classifier":sum(p.numel() for p in self.classifier.parameters())}; total=sum(p.numel() for p in self.parameters()); trainable=sum(p.numel() for p in self.parameters() if p.requires_grad); return {"total":total,"trainable":trainable,"frozen":total-trainable,"components":components}
    def assert_freeze_policy(self):
        assert all(not p.requires_grad for p in self.semantic.stem.parameters()); assert all(not p.requires_grad for s in self.semantic.stages[:3] for p in s.parameters()); assert all(p.requires_grad for p in self.semantic.stages[3].parameters()); assert all(p.requires_grad for p in self.semantic.head.parameters())
