import tempfile, unittest
from pathlib import Path
import torch
from torch import nn
from src.models.edge_branch import EdgeBranch
from src.models.convnext_edge import ConvNeXtEdge

class M5EdgeTests(unittest.TestCase):
    def test_canonical_fixed_sobel_and_shape(self):
        branch=EdgeBranch(); self.assertEqual(tuple(branch.sobel_x.flatten().tolist()),(-1.,0.,1.,-2.,0.,2.,-1.,0.,1.)); self.assertEqual(tuple(branch.sobel_y.flatten().tolist()),(-1.,-2.,-1.,0.,0.,0.,1.,2.,1.)); self.assertEqual(tuple(branch(torch.randn(2,3,384,384)).shape),(2,32)); self.assertNotIn("sobel_x",dict(branch.named_parameters()))
    def test_full_smoke_gradients_and_checkpoint(self):
        model=ConvNeXtEdge(pretrained=False); model.assert_freeze_policy(); model.train(); images=torch.randn(2,3,384,384); labels=torch.tensor([0,2]); logits,f=model(images,return_features=True)
        self.assertEqual(tuple(f["edge"].shape),(2,32)); self.assertEqual(tuple(f["semantic_projected"].shape),(2,256)); self.assertEqual(tuple(f["edge_projected"].shape),(2,256)); self.assertEqual(tuple(f["combined"].shape),(2,256)); self.assertEqual(tuple(logits.shape),(2,3))
        optimizer=torch.optim.AdamW(model.optimizer_parameter_groups(),weight_decay=.01); nn.CrossEntropyLoss(weight=torch.tensor([1.,1.1,.9]))(logits,labels).backward(); self.assertTrue(torch.all(model.branch_logits.grad.abs()>0)); self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in model.edge.parameters())); self.assertIsNone(model.edge.sobel_x.grad); self.assertIsNone(model.edge.sobel_y.grad); optimizer.step()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"c.pt"; torch.save({"model":model.state_dict()},p); clone=ConvNeXtEdge(pretrained=False); clone.load_state_dict(torch.load(p,weights_only=True)["model"])
if __name__=="__main__": unittest.main()
