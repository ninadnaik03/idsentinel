"""Train/evaluate the approved M5 ConvNeXt + fixed-Sobel edge experiment."""
from __future__ import annotations
import argparse,csv,json,platform,sys,time
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt, numpy as np, psutil, timm, torch
from torch import nn
from torch.utils.data import Subset
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts.train_m4_texture import seed_everything,loader,git_commit,fit_cuda_batch,run_epoch
from src.data.baseline import CLASS_NAMES,ProtocolAReducedDataset,load_and_validate_manifest,training_class_weights
from src.models.backbone import MODEL_NAME
from src.models.convnext_edge import ConvNeXtEdge
from src.training.metrics import classification_metrics

@torch.no_grad()
def predict(model,data_loader,device):
    model.eval(); out=[]
    for images,labels,indices in data_loader:
        device_images=images.to(device); logits,f=model(device_images,return_features=True); probs=logits.softmax(1).cpu(); gray,mag=model.edge.edge_maps(device_images)
        for pos,(target,index,prob) in enumerate(zip(labels.tolist(),indices.tolist(),probs.tolist(),strict=True)):
            norms={k+"_norm":float(f[k][pos].norm().cpu()) for k in ("edge","semantic_projected","edge_projected","combined")}; h,w=mag.shape[-2:]; bh,bw=max(1,int(round(h*.1))),max(1,int(round(w*.1))); mask=torch.ones((h,w),dtype=torch.bool,device=device); mask[bh:h-bh,bw:w-bw]=False; center=mag[pos,0,bh:h-bh,bw:w-bw]
            norms.update({"border_sobel_mean":float(mag[pos,0][mask].mean().cpu()),"central_sobel_mean":float(center.mean().cpu())}); out.append((index,target,int(np.argmax(prob)),prob,norms,gray[pos,0].cpu(),mag[pos,0].cpu()))
    return out

def plots(history,metrics,failures,test_set,rows):
    out=ROOT/"artifacts/plots"; out.mkdir(parents=True,exist_ok=True); epochs=[r["epoch"] for r in history]
    fig,axes=plt.subplots(1,2,figsize=(10,4)); axes[0].plot(epochs,[r["train"]["loss"] for r in history],label="train"); axes[0].plot(epochs,[r["validation"]["loss"] for r in history],label="validation"); axes[0].set_title("Loss"); axes[0].legend(); axes[1].plot(epochs,[r["train"]["macro_f1"] for r in history],label="train"); axes[1].plot(epochs,[r["validation"]["macro_f1"] for r in history],label="validation"); axes[1].set_title("Macro F1"); axes[1].legend(); fig.tight_layout(); fig.savefig(out/"m5_training_curves.png",dpi=160); plt.close(fig)
    values=[x for r in history for x in r["branch_weights"]]; lo,hi=min(values),max(values); margin=max(.001,(hi-lo)*.2); fig,ax=plt.subplots(figsize=(6,4)); ax.plot(epochs,[r["branch_weights"][0] for r in history],label="semantic"); ax.plot(epochs,[r["branch_weights"][1] for r in history],label="edge"); ax.set_ylim(lo-margin,hi+margin); ax.set_xlabel("Epoch"); ax.set_ylabel("Learned fusion weight"); ax.legend(); fig.tight_layout(); fig.savefig(out/"m5_branch_weights.png",dpi=160); plt.close(fig)
    matrix=metrics["confusion_matrix"]; fig,ax=plt.subplots(figsize=(5,4)); im=ax.imshow(matrix,cmap="Blues")
    for i in range(3):
        for j in range(3): ax.text(j,i,matrix[i][j],ha="center",va="center")
    ax.set_xticks(range(3),CLASS_NAMES,rotation=25); ax.set_yticks(range(3),CLASS_NAMES); ax.set_xlabel("Predicted"); ax.set_ylabel("True"); fig.colorbar(im); fig.tight_layout(); fig.savefig(out/"m5_confusion_matrix.png",dpi=160); plt.close(fig)
    from PIL import Image
    if failures:
        cols,n=4,len(failures); fig,axes=plt.subplots((n+3)//4,cols,figsize=(12,((n+3)//4)*3.4),squeeze=False); byid={r["sample_id"]:r for r in test_set.records}
        for ax,f in zip(axes.flat,failures): ax.imshow(Image.open(byid[f["sample_id"]]["portrait_crop_path"]).convert("RGB")); ax.set_title(f'{f["true_class"]}->{f["predicted_class"]}\n{f["comparison_to_m3"]}',fontsize=8); ax.axis("off")
        for ax in axes.flat[n:]: ax.axis("off")
        fig.tight_layout(); fig.savefig(out/"m5_failures.png",dpi=150); plt.close(fig)
    # Deterministic representative set: first correct and first failure by manifest order for each class when available.
    selected=[]
    for target,name in enumerate(CLASS_NAMES):
        class_rows=[r for r in rows if r[1]==target]; selected.extend(([next((r for r in class_rows if r[1]==r[2]),class_rows[0])],[next((r for r in class_rows if r[1]!=r[2]),class_rows[-1])]))
    selected=[item for pair in selected for item in pair]; fig,axes=plt.subplots(len(selected),3,figsize=(9,len(selected)*2.5),squeeze=False)
    for row,axrow in zip(selected,axes):
        index,target,pred,_,_,gray,mag=row; record=test_set.records[index]; axrow[0].imshow(Image.open(record["portrait_crop_path"]).convert("RGB")); axrow[1].imshow(gray,cmap="gray"); axrow[2].imshow(mag,cmap="magma"); axrow[0].set_ylabel(f'{CLASS_NAMES[target]}\n{"correct" if target==pred else "failure"}')
        for ax,title in zip(axrow,("Original","Grayscale","Sobel magnitude")): ax.set_title(title); ax.axis("off")
    fig.tight_layout(); fig.savefig(out/"m5_edge_examples.png",dpi=150); plt.close(fig)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--manifest",type=Path,default=ROOT/"artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"); p.add_argument("--output-dir",type=Path,default=ROOT/"artifacts/m5"); p.add_argument("--device",default="cuda" if torch.cuda.is_available() else "cpu"); p.add_argument("--batch-size",type=int,default=8); p.add_argument("--accumulation",type=int,default=4); p.add_argument("--workers",type=int,default=2); p.add_argument("--epochs",type=int,default=250); p.add_argument("--seed",type=int,default=20250813); p.add_argument("--patience",type=int,default=15); p.add_argument("--smoke",action="store_true"); p.add_argument("--no-pretrained",action="store_true"); args=p.parse_args(); seed_everything(args.seed)
    records,integrity=load_and_validate_manifest(args.manifest)
    if len(records)!=300 or len({r["sample_id"] for r in records})!=300 or not all(Path(r["portrait_crop_path"]).exists() for r in records): raise RuntimeError("Frozen M5 manifest invariant failed")
    device=torch.device(args.device)
    if args.smoke: args.device,args.batch_size,args.accumulation,args.workers,args.epochs,device,args.output_dir="cpu",2,1,0,1,torch.device("cpu"),ROOT/"artifacts/smoke/m5"
    train=ProtocolAReducedDataset(records,"train",training=True); val=ProtocolAReducedDataset(records,"validation")
    if args.smoke: train,val=Subset(train,[0,1]),Subset(val,[0,15])
    started=time.perf_counter(); proc=psutil.Process(); before=proc.memory_info().rss; model=ConvNeXtEdge(pretrained=not args.no_pretrained).to(device); model.assert_freeze_policy(); params=model.parameter_summary()
    if device.type=="cuda": args.batch_size=fit_cuda_batch(model,args.batch_size); args.accumulation=max(args.accumulation,int(np.ceil(32/args.batch_size)))
    train_loader=loader(train,args.batch_size,True,args.workers,args.seed); val_loader=loader(val,args.batch_size,False,args.workers,args.seed); weights=torch.tensor(training_class_weights(records),dtype=torch.float32,device=device); criterion=nn.CrossEntropyLoss(weight=weights); optimizer=torch.optim.AdamW(model.optimizer_parameter_groups(),weight_decay=.01); scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode="max",patience=5,factor=.5); scaler=torch.amp.GradScaler("cuda") if device.type=="cuda" else None
    args.output_dir.mkdir(parents=True,exist_ok=True); checkpoint=args.output_dir/"best_convnext_edge.pt"; history=[]; best=-1.; best_epoch=stale=0
    with torch.no_grad(): probe=next(iter(val_loader))[0][:1].to(device); tick=time.perf_counter(); model.eval()(probe); latency=time.perf_counter()-tick
    for epoch in range(1,args.epochs+1):
        tr=run_epoch(model,train_loader,criterion,device,optimizer,args.accumulation,scaler); va=run_epoch(model,val_loader,criterion,device); scheduler.step(va["macro_f1"]); learned=model.branch_logits.softmax(0).detach().cpu().tolist(); history.append({"epoch":epoch,"train":tr,"validation":va,"learning_rates":{g["name"]:g["lr"] for g in optimizer.param_groups},"branch_weights":learned})
        if va["macro_f1"]>best: best,best_epoch,stale=va["macro_f1"],epoch,0; torch.save({"model":model.state_dict(),"epoch":epoch,"validation_macro_f1":best,"manifest_sha256":integrity["manifest_sha256"],"class_names":CLASS_NAMES,"branch_weights":learned},checkpoint)
        else: stale+=1
        if stale>=args.patience: break
    loaded=torch.load(checkpoint,map_location=device,weights_only=True); model.load_state_dict(loaded["model"]); best_weights=model.branch_logits.softmax(0).detach().cpu().tolist(); meta={"protocol":"Protocol A-Reduced","experiment":"M5 ConvNeXt + Edge","smoke_test":args.smoke,"seed":args.seed,"config":vars(args)|{"manifest":str(args.manifest),"output_dir":str(args.output_dir)},"manifest_sha256":integrity["manifest_sha256"],"git_commit":git_commit(),"python":sys.version,"torch":torch.__version__,"timm":timm.__version__,"device":str(device),"device_name":torch.cuda.get_device_name(0) if device.type=="cuda" else platform.processor(),"model_name":MODEL_NAME,"class_weights_train_only":weights.cpu().tolist(),"parameters":params,"best_epoch":best_epoch,"best_validation_macro_f1":best,"best_checkpoint_branch_weights":{"semantic":best_weights[0],"edge":best_weights[1]},"epochs_completed":len(history),"duration_seconds":time.perf_counter()-started,"peak_rss_bytes":max(before,getattr(proc.memory_info(),"peak_wset",proc.memory_info().rss)),"single_forward_seconds":latency,"augmentation":[],"history":history}; (args.output_dir/"run_metadata.json").write_text(json.dumps(meta,indent=2,default=str),encoding="utf-8")
    if args.smoke: print(json.dumps(meta,indent=2,default=str)); return 0
    test=ProtocolAReducedDataset(records,"test"); rows=predict(model,loader(test,args.batch_size,False,args.workers,args.seed),device); m3m=json.loads((ROOT/"artifacts/metrics/m3_baseline_metrics.json").read_text()); m4m=json.loads((ROOT/"artifacts/metrics/m4_texture_metrics.json").read_text()); m3={r["sample_id"]:r for r in csv.DictReader((ROOT/"artifacts/metrics/m3_test_predictions.csv").open())}; m4={r["sample_id"]:r for r in csv.DictReader((ROOT/"artifacts/metrics/m4_test_predictions.csv").open())}; metrics=classification_metrics([r[1] for r in rows],[r[2] for r in rows]); failures=[]; padding={True:[0,0],False:[0,0]}; classpad=defaultdict(lambda:[0,0]); border=defaultdict(list)
    path=ROOT/"artifacts/metrics/m5_test_predictions.csv"; fields=["sample_id","base_document_id","true_class","predicted_class",*[f"p_{c}" for c in CLASS_NAMES],"confidence","padded","crop_path","comparison_to_m3","comparison_to_m4","edge_norm","semantic_projected_norm","edge_projected_norm","combined_norm","border_sobel_mean","central_sobel_mean"]
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
        for index,target,pred,prob,norms,_,_ in rows:
            rec=test.records[index]; sid=rec["sample_id"]; err=target!=pred; m3err=m3[sid]["true_class"]!=m3[sid]["predicted_class"]; status="CORRECTED" if not err and m3err else "PERSISTENT" if err and m3err and m3[sid]["predicted_class"]==CLASS_NAMES[pred] else "CHANGED_TO_DIFFERENT_WRONG_CLASS" if err and m3err else "NEW_FAILURE" if err else "CORRECT_BOTH"; padded=bool(rec["portrait_padding_applied"]); padding[padded][0]+=int(err); padding[padded][1]+=1; classpad[(rec["mapped_label"],padded)][0 if err else 1]+=1
            if padded: border[rec["mapped_label"]].append({"sample_id":sid,"border_sobel_mean":norms["border_sobel_mean"],"central_sobel_mean":norms["central_sobel_mean"],"ratio":norms["border_sobel_mean"]/norms["central_sobel_mean"] if norms["central_sobel_mean"] else None})
            row={"sample_id":sid,"base_document_id":rec["base_document_id"],"true_class":CLASS_NAMES[target],"predicted_class":CLASS_NAMES[pred],**{f"p_{c}":prob[i] for i,c in enumerate(CLASS_NAMES)},"confidence":max(prob),"padded":padded,"crop_path":rec["portrait_crop_path"],"comparison_to_m3":status,"comparison_to_m4":"same" if CLASS_NAMES[pred]==m4[sid]["predicted_class"] else "different",**norms}; writer.writerow(row)
            if err: failures.append(row)
    border_summary={c:{"count":len(v),"mean_border":float(np.mean([x["border_sobel_mean"] for x in v])),"mean_central":float(np.mean([x["central_sobel_mean"] for x in v])),"mean_ratio":float(np.mean([x["ratio"] for x in v])),"samples":v} for c,v in border.items()}; metrics.update({"protocol":"Protocol A-Reduced","best_epoch":best_epoch,"best_validation_macro_f1":best,"learned_fusion_weights":{"semantic":best_weights[0],"edge":best_weights[1]},"test_errors":len(failures),"padding_diagnostic":{str(k).lower():{"errors":v[0],"count":v[1],"error_rate":v[0]/v[1]} for k,v in padding.items()},"class_by_padding":{f"{k[0]}|padded={str(k[1]).lower()}":{"errors":v[0],"correct":v[1],"count":sum(v)} for k,v in classpad.items()},"border_sensitivity":border_summary,"failures":failures,"reproducibility":meta}); (ROOT/"artifacts/metrics/m5_edge_metrics.json").write_text(json.dumps(metrics,indent=2,default=str),encoding="utf-8")
    compact=lambda m:{"accuracy":m["accuracy"],"macro_f1":m["macro_f1"],"per_class_f1":dict(zip(CLASS_NAMES,m["per_class_f1"],strict=True)),"failures":m["test_errors"]}; delta={"accuracy":metrics["accuracy"]-m3m["accuracy"],"macro_f1":metrics["macro_f1"]-m3m["macro_f1"],"per_class_f1":{c:metrics["per_class_f1"][i]-m3m["per_class_f1"][i] for i,c in enumerate(CLASS_NAMES)}}; (ROOT/"artifacts/metrics/m5_vs_m3.json").write_text(json.dumps({"m3":compact(m3m),"m5":compact(metrics),"delta_m5_minus_m3":delta},indent=2),encoding="utf-8"); (ROOT/"artifacts/metrics/m5_model_comparison.json").write_text(json.dumps({"M3 Semantic":compact(m3m),"M4 +Texture":compact(m4m),"M5 +Edge":compact(metrics)},indent=2),encoding="utf-8"); plots(history,metrics,failures,test,rows); print(json.dumps({"metrics":metrics,"delta":delta},indent=2,default=str)); return 0
if __name__=="__main__": raise SystemExit(main())
