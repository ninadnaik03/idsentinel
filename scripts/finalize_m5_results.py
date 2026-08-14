"""Validate imported M5 results and generate required reports."""
from __future__ import annotations
import csv,hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]; N=("BONA_FIDE","PRINT","SCREEN")
sys.path.insert(0,str(ROOT))
def probs(r): return ", ".join(f"{c}={float(r['p_'+c]):.6f}" for c in N)
def main():
    m3m=json.loads((ROOT/"artifacts/metrics/m3_baseline_metrics.json").read_text()); m4m=json.loads((ROOT/"artifacts/metrics/m4_texture_metrics.json").read_text()); m5m=json.loads((ROOT/"artifacts/metrics/m5_edge_metrics.json").read_text()); meta=json.loads((ROOT/"artifacts/m5/run_metadata.json").read_text()); comp=json.loads((ROOT/"artifacts/metrics/m5_model_comparison.json").read_text()); delta=json.loads((ROOT/"artifacts/metrics/m5_vs_m3.json").read_text())["delta_m5_minus_m3"]
    read=lambda p:{r["sample_id"]:r for r in csv.DictReader((ROOT/p).open(encoding="utf-8"))}; m3=read("artifacts/metrics/m3_test_predictions.csv"); m4=read("artifacts/metrics/m4_test_predictions.csv"); m5=read("artifacts/metrics/m5_test_predictions.csv")
    if len(m5)!=44: raise RuntimeError("M5 test row count is not 44")
    if set(m3)!=set(m4) or set(m3)!=set(m5): raise RuntimeError("Frozen test IDs differ")
    ck=torch.load(ROOT/"artifacts/m5/best_convnext_edge.pt",map_location="cpu",weights_only=True); gpu_hash=json.loads((ROOT/"artifacts/m3/frozen_manifest_provenance.json").read_text())["gpu_bundle_manifest_sha256"]
    if ck["manifest_sha256"]!=meta["manifest_sha256"] or meta["manifest_sha256"]!=gpu_hash: raise RuntimeError("M5 provenance mismatch")
    if sum(sum(x) for x in m5m["confusion_matrix"])!=44 or m5m["test_errors"]!=sum(r["true_class"]!=r["predicted_class"] for r in m5.values()): raise RuntimeError("M5 metric invariant failed")
    transitions=defaultdict(Counter); m3_fail=[]
    for sid,a in m3.items():
        b=m5[sid]; aerr=a["true_class"]!=a["predicted_class"]; berr=b["true_class"]!=b["predicted_class"]
        if aerr:
            state="CORRECTED" if not berr else "PERSISTENT" if b["predicted_class"]==a["predicted_class"] else "CHANGED_TO_DIFFERENT_WRONG_CLASS"; transitions[f"{a['true_class']}->{a['predicted_class']}"][state]+=1; m3_fail.append((sid,state))
    new=sum(a["true_class"]==a["predicted_class"] and m5[sid]["true_class"]!=m5[sid]["predicted_class"] for sid,a in m3.items())
    failure_categories=Counter()
    for sid,e in m5.items():
        if e["true_class"]==e["predicted_class"]: continue
        m3ok=m3[sid]["true_class"]==m3[sid]["predicted_class"]; m4ok=m4[sid]["true_class"]==m4[sid]["predicted_class"]
        category="NEW_EDGE_FAILURE" if m3ok else "CORRECTED_BY_TEXTURE_ONLY" if m4ok else "PERSISTENT_ACROSS_ALL"; failure_categories[category]+=1
    overlap=Counter()
    for sid,a in m3.items():
        if a["true_class"]==a["predicted_class"]: continue
        edge_ok=m5[sid]["true_class"]==m5[sid]["predicted_class"]; texture_ok=m4[sid]["true_class"]==m4[sid]["predicted_class"]
        overlap["CORRECTED_BY_BOTH" if edge_ok and texture_ok else "CORRECTED_BY_EDGE_ONLY" if edge_ok else "CORRECTED_BY_TEXTURE_ONLY" if texture_ok else "PERSISTENT_ACROSS_ALL"]+=1
    table=["| Metric | M3 Semantic | M4 +Texture | M5 +Edge |","|---|---:|---:|---:|"]
    for label,key in (("Accuracy","accuracy"),("Macro-F1","macro_f1")): table.append(f"| {label} | {comp['M3 Semantic'][key]:.6f} | {comp['M4 +Texture'][key]:.6f} | {comp['M5 +Edge'][key]:.6f} |")
    for c in N: table.append(f"| {c} F1 | {comp['M3 Semantic']['per_class_f1'][c]:.6f} | {comp['M4 +Texture']['per_class_f1'][c]:.6f} | {comp['M5 +Edge']['per_class_f1'][c]:.6f} |")
    table.append(f"| Failures | {comp['M3 Semantic']['failures']} | {comp['M4 +Texture']['failures']} | {comp['M5 +Edge']['failures']} |")
    border=m5m["border_sensitivity"]
    report=["# M5 ConvNeXt + Edge Report","","These are our observed Protocol A-Reduced results, not paper results or a full-DLC reproduction.","","## Controlled implementation","",f"- Frozen 300-sample GPU manifest SHA-256 `{meta['manifest_sha256']}`, identical to M3/M4 provenance.","- Pixels only; no texture branch or acquisition/detector/padding metadata enters the classifier.","- Canonical fixed Sobel-X/Y buffers, luminance grayscale, magnitude `sqrt(gx^2 + gy^2 + 1e-6)`, no per-image normalization; trainable Conv-BN-ReLU 1->16->32, global pool, Linear 32->32.","- Semantic and 32-D edge features project to 256-D, combine through two softmax-normalized learned weights, then classifier 256->512->256->128->3.",f"- Parameters: {meta['parameters']['total']:,} total; {meta['parameters']['trainable']:,} trainable; {meta['parameters']['frozen']:,} frozen.",f"- Tesla T4; duration {meta['duration_seconds']:.2f} s; {meta['epochs_completed']} epochs; best epoch {meta['best_epoch']}; no stochastic augmentation.","","## Observed results","",f"- Best validation macro-F1: {m5m['best_validation_macro_f1']:.6f}.",f"- Test accuracy {m5m['accuracy']:.6f}; macro precision {m5m['macro_precision']:.6f}; macro recall {m5m['macro_recall']:.6f}; macro-F1 {m5m['macro_f1']:.6f}.",*[f"- {c}: precision {m5m['per_class_precision'][i]:.6f}; recall {m5m['per_class_recall'][i]:.6f}; F1 {m5m['per_class_f1'][i]:.6f}." for i,c in enumerate(N)],f"- Confusion matrix: `{m5m['confusion_matrix']}`; failures {m5m['test_errors']}/44.","","## M5 versus M3 (primary)","",f"- Accuracy {delta['accuracy']:+.6f}; macro-F1 {delta['macro_f1']:+.6f}.",*[f"- {c} F1 {delta['per_class_f1'][c]:+.6f}." for c in N],"","## Observed three-model comparison","",*table,"","M4 is descriptively higher than M5 on this one 44-sample test (accuracy +0.045455 and macro-F1 +0.038269 for M4 relative to M5). This does not establish that texture is objectively superior to edge.","","## Learned fusion weights","",f"- Semantic {m5m['learned_fusion_weights']['semantic']:.6f}; edge {m5m['learned_fusion_weights']['edge']:.6f}. These are learned fusion weights, not causal importance.","","## M3 failure transitions","",*[f"- {k}: "+", ".join(f"{state}={count}" for state,count in v.items()) for k,v in transitions.items()],f"- New M5 failures among M3-correct samples: {new}.",f"- Correction overlap across the 18 M3 failures: `{dict(overlap)}`.","","## Padding and border diagnostics","",f"- Padded: {m5m['padding_diagnostic']['true']['errors']}/22 ({m5m['padding_diagnostic']['true']['error_rate']:.2%}); M3 {m3m['padding_diagnostic']['true']['error_rate']:.2%}; M4 {m4m['padding_diagnostic']['true']['error_rate']:.2%}.",f"- Non-padded: {m5m['padding_diagnostic']['false']['errors']}/22 ({m5m['padding_diagnostic']['false']['error_rate']:.2%}); M3 {m3m['padding_diagnostic']['false']['error_rate']:.2%}; M4 {m4m['padding_diagnostic']['false']['error_rate']:.2%}.",*[f"- Padded {c}: n={border[c]['count']}; mean outer-border Sobel={border[c]['mean_border']:.6f}; mean central Sobel={border[c]['mean_central']:.6f}; mean per-sample ratio={border[c]['mean_ratio']:.6f}." for c in N],"","These are small descriptive distributions and do not show that reflected padding caused predictions.","","## Limitations","","- Only 44 test samples and one primary seed; differences have high sampling uncertainty.","- ConvNeXt+Edge also adds projections and a progressive classifier, so this is not a causal edge-only ablation.","- Sobel is applied to ImageNet-normalized inputs; absolute magnitude therefore reflects that fixed normalization.","- Protocol A-Reduced is not the full DLC-2021 corpus.","","## Proposed M6 plan (not implemented)","","If explicitly approved, M6 should combine the already frozen M5 edge and M4 texture designs with the semantic branch in a three-branch model: 64-D texture and 32-D edge outputs, three independent 256-D projections, three softmax-normalized learned weights, and the same progressive classifier. It should reuse the exact frozen manifest/seed/preprocessing and semantic freeze policy, pass a three-branch CPU gradient/checkpoint gate, then run one validation-selected T4 experiment and one frozen-test evaluation. Compare descriptively with M3, M4, and M5, retain padding/border/failure analyses, and do not add API, frontend, deployment, robustness, unconstrained-weight ablation, or extra seeds unless separately approved."]
    (ROOT/"docs/M5_EDGE_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    failure=["# M5 Failure Analysis","",f"M5 failures: {m5m['test_errors']}/44. Categories: `{dict(failure_categories)}`.",""]
    for sid,e in m5.items():
        if e["true_class"]==e["predicted_class"]: continue
        m3ok=m3[sid]["true_class"]==m3[sid]["predicted_class"]; m4ok=m4[sid]["true_class"]==m4[sid]["predicted_class"]; cat="NEW_EDGE_FAILURE" if m3ok else "CORRECTED_BY_TEXTURE_ONLY" if m4ok else "PERSISTENT_ACROSS_ALL"
        failure += [f"## `{sid}`","",f"- `{e['true_class']}` -> `{e['predicted_class']}`; confidence {float(e['confidence']):.6f}; {cat}.",f"- Probabilities: {probs(e)}.",f"- Padding `{e['padded']}`; edge norm {float(e['edge_norm']):.6f}; crop `{e['crop_path']}`.","- No causal explanation is inferred.",""]
    (ROOT/"docs/M5_FAILURE_ANALYSIS.md").write_text("\n".join(failure),encoding="utf-8")
    # Re-render deterministic correct/failure Sobel examples with explicit row labels.
    import matplotlib.pyplot as plt
    from PIL import Image
    from src.data.baseline import ProtocolAReducedDataset,load_and_validate_manifest
    from src.models.edge_branch import EdgeBranch
    records,_=load_and_validate_manifest(ROOT/"artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"); test=ProtocolAReducedDataset(records,"test"); byid={r["sample_id"]:(i,r) for i,r in enumerate(test.records)}; selected=[]
    for c in N:
        rows=[r for r in m5.values() if r["true_class"]==c]; selected += [next((r for r in rows if r["true_class"]==r["predicted_class"]),rows[0]),next((r for r in rows if r["true_class"]!=r["predicted_class"]),rows[-1])]
    edge=__import__("src.models.edge_branch",fromlist=["EdgeBranch"]).EdgeBranch().eval(); fig,axes=plt.subplots(6,3,figsize=(9,15),squeeze=False)
    with torch.no_grad():
        for row,axrow in zip(selected,axes):
            index,record=byid[row["sample_id"]]; tensor,_,_=test[index]; gray,mag=edge.edge_maps(tensor.unsqueeze(0)); outcome="correct" if row["true_class"]==row["predicted_class"] else "failure"; axrow[0].imshow(Image.open(record["portrait_crop_path"]).convert("RGB")); axrow[1].imshow(gray[0,0],cmap="gray"); axrow[2].imshow(mag[0,0],cmap="magma");
            for ax,title in zip(axrow,(f"{row['true_class']} — {outcome}\nOriginal","Grayscale","Sobel magnitude")): ax.set_title(title); ax.axis("off")
    fig.tight_layout(); fig.savefig(ROOT/"artifacts/plots/m5_edge_examples.png",dpi=150); plt.close(fig)
    print(json.dumps({"transitions":{k:dict(v) for k,v in transitions.items()},"new_failures":new,"failure_categories":dict(failure_categories),"correction_overlap":dict(overlap)},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
