"""Train and evaluate the approved M4 ConvNeXt + texture experiment."""

from __future__ import annotations

import argparse, csv, hashlib, json, platform, random, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import psutil
import timm
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.baseline import CLASS_NAMES, ProtocolAReducedDataset, load_and_validate_manifest, training_class_weights
from src.models.backbone import MODEL_NAME
from src.models.convnext_texture import ConvNeXtTexture
from src.training.metrics import classification_metrics

M3_METRICS = ROOT / "artifacts/metrics/m3_baseline_metrics.json"
M3_PREDICTIONS = ROOT / "artifacts/metrics/m3_test_predictions.csv"


def seed_everything(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def loader(dataset, batch_size, shuffle, workers, seed):
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=workers,
                      generator=torch.Generator().manual_seed(seed), pin_memory=torch.cuda.is_available())


def git_commit():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return None


def fit_cuda_batch(model, requested):
    for candidate in [n for n in (requested, 8, 4, 2, 1) if n <= requested]:
        try:
            model.train(); model.zero_grad(set_to_none=True)
            model(torch.zeros(candidate, 3, 384, 384, device="cuda")).sum().backward()
            model.zero_grad(set_to_none=True); torch.cuda.empty_cache(); return candidate
        except (torch.OutOfMemoryError, ValueError):
            model.zero_grad(set_to_none=True); torch.cuda.empty_cache()
    raise RuntimeError("M4 backward pass does not fit CUDA batch size 1")


def run_epoch(model, data_loader, criterion, device, optimizer=None, accumulation=1, scaler=None):
    training = optimizer is not None; model.train(training); targets, predictions, losses = [], [], []
    if training: optimizer.zero_grad(set_to_none=True)
    for step, (images, labels, _) in enumerate(data_loader):
        images, labels = images.to(device), labels.to(device)
        with torch.autocast(device_type=device.type, enabled=scaler is not None):
            logits = model(images); loss = criterion(logits, labels)
        if training:
            scaled = loss / accumulation
            (scaler.scale(scaled) if scaler else scaled).backward()
            if (step + 1) % accumulation == 0 or step + 1 == len(data_loader):
                if scaler: scaler.step(optimizer); scaler.update()
                else: optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach())); targets += labels.cpu().tolist(); predictions += logits.argmax(1).detach().cpu().tolist()
    result = classification_metrics(targets, predictions); result["loss"] = float(np.mean(losses)); return result


@torch.no_grad()
def predict(model, data_loader, device):
    model.eval(); output = []
    for images, labels, indices in data_loader:
        logits, features = model(images.to(device), return_features=True); probabilities = logits.softmax(1).cpu()
        for position, (target, index, probability) in enumerate(zip(labels.tolist(), indices.tolist(), probabilities.tolist(), strict=True)):
            norms = {key + "_norm": float(features[key][position].norm().cpu()) for key in ("semantic", "texture", "semantic_projected", "texture_projected", "combined")}
            output.append((index, target, int(np.argmax(probability)), probability, norms))
    return output


def save_plots(history, metrics, failures, test_set):
    plots = ROOT / "artifacts/plots"; plots.mkdir(parents=True, exist_ok=True); epochs = [r["epoch"] for r in history]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(epochs, [r["train"]["loss"] for r in history], label="train"); axes[0].plot(epochs, [r["validation"]["loss"] for r in history], label="validation"); axes[0].set_title("Loss"); axes[0].legend()
    axes[1].plot(epochs, [r["train"]["macro_f1"] for r in history], label="train"); axes[1].plot(epochs, [r["validation"]["macro_f1"] for r in history], label="validation"); axes[1].set_title("Macro F1"); axes[1].legend(); fig.tight_layout(); fig.savefig(plots / "m4_training_curves.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4)); ax.plot(epochs, [r["branch_weights"][0] for r in history], label="semantic"); ax.plot(epochs, [r["branch_weights"][1] for r in history], label="texture"); ax.set_ylim(0, 1); ax.set_xlabel("Epoch"); ax.set_ylabel("Learned fusion weight"); ax.legend(); fig.tight_layout(); fig.savefig(plots / "m4_branch_weights.png", dpi=160); plt.close(fig)
    matrix = metrics["confusion_matrix"]; fig, ax = plt.subplots(figsize=(5, 4)); image = ax.imshow(matrix, cmap="Blues")
    for row in range(3):
        for col in range(3): ax.text(col, row, matrix[row][col], ha="center", va="center")
    ax.set_xticks(range(3), CLASS_NAMES, rotation=25); ax.set_yticks(range(3), CLASS_NAMES); ax.set_xlabel("Predicted"); ax.set_ylabel("True"); fig.colorbar(image); fig.tight_layout(); fig.savefig(plots / "m4_confusion_matrix.png", dpi=160); plt.close(fig)
    if failures:
        from PIL import Image
        columns, rows = 4, (len(failures) + 3) // 4; fig, axes = plt.subplots(rows, columns, figsize=(12, rows * 3.4), squeeze=False)
        by_id = {r["sample_id"]: r for r in test_set.records}
        for ax, failure in zip(axes.flat, failures):
            ax.imshow(Image.open(by_id[failure["sample_id"]]["portrait_crop_path"]).convert("RGB")); ax.set_title(f'{failure["true_class"]} -> {failure["predicted_class"]}\n{failure["comparison_to_m3"]}', fontsize=8); ax.axis("off")
        for ax in axes.flat[len(failures):]: ax.axis("off")
        fig.tight_layout(); fig.savefig(plots / "m4_failures.png", dpi=150); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, default=ROOT / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl"); parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/m4")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu"); parser.add_argument("--batch-size", type=int, default=8); parser.add_argument("--accumulation", type=int, default=4); parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=250); parser.add_argument("--seed", type=int, default=20250813); parser.add_argument("--patience", type=int, default=15); parser.add_argument("--smoke", action="store_true"); parser.add_argument("--no-pretrained", action="store_true")
    args = parser.parse_args(); seed_everything(args.seed); records, integrity = load_and_validate_manifest(args.manifest)
    if len(records) != 300: raise RuntimeError("M4 requires the frozen 300-record manifest")
    if not all(Path(r["portrait_crop_path"]).exists() for r in records): raise RuntimeError("One or more manifest crop paths do not exist")
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
    if args.smoke: args.device, args.batch_size, args.accumulation, args.workers, args.epochs, device, args.output_dir = "cpu", 2, 1, 0, 1, torch.device("cpu"), ROOT / "artifacts/smoke/m4"
    train_set = ProtocolAReducedDataset(records, "train", training=True); validation_set = ProtocolAReducedDataset(records, "validation")
    if args.smoke: train_set, validation_set = Subset(train_set, [0, 1]), Subset(validation_set, [0, 15])
    started = time.perf_counter(); process = psutil.Process(); before_rss = process.memory_info().rss
    model = ConvNeXtTexture(pretrained=not args.no_pretrained).to(device); model.assert_freeze_policy(); parameter_summary = model.parameter_summary()
    if device.type == "cuda": args.batch_size = fit_cuda_batch(model, args.batch_size); args.accumulation = max(args.accumulation, int(np.ceil(32 / args.batch_size)))
    train_loader = loader(train_set, args.batch_size, True, args.workers, args.seed); validation_loader = loader(validation_set, args.batch_size, False, args.workers, args.seed)
    weights = torch.tensor(training_class_weights(records), dtype=torch.float32, device=device); criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.optimizer_parameter_groups(), weight_decay=0.01); scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", patience=5, factor=0.5); scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None
    args.output_dir.mkdir(parents=True, exist_ok=True); checkpoint = args.output_dir / "best_convnext_texture.pt"; history, best_f1, best_epoch, stale = [], -1.0, 0, 0
    with torch.no_grad():
        probe = next(iter(validation_loader))[0][:1].to(device); tick = time.perf_counter(); model.eval()(probe); forward_latency = time.perf_counter() - tick
    for epoch in range(1, args.epochs + 1):
        train_metrics = run_epoch(model, train_loader, criterion, device, optimizer, args.accumulation, scaler); validation_metrics = run_epoch(model, validation_loader, criterion, device); scheduler.step(validation_metrics["macro_f1"])
        learned = model.branch_logits.softmax(0).detach().cpu().tolist(); history.append({"epoch": epoch, "train": train_metrics, "validation": validation_metrics, "learning_rates": {g["name"]: g["lr"] for g in optimizer.param_groups}, "branch_weights": learned})
        if validation_metrics["macro_f1"] > best_f1:
            best_f1, best_epoch, stale = validation_metrics["macro_f1"], epoch, 0
            torch.save({"model": model.state_dict(), "epoch": epoch, "validation_macro_f1": best_f1, "manifest_sha256": integrity["manifest_sha256"], "class_names": CLASS_NAMES, "branch_weights": learned}, checkpoint)
        else: stale += 1
        if stale >= args.patience: break
    loaded = torch.load(checkpoint, map_location=device, weights_only=True); model.load_state_dict(loaded["model"]); best_weights = model.branch_logits.softmax(0).detach().cpu().tolist()
    metadata = {"protocol": "Protocol A-Reduced", "experiment": "M4 ConvNeXt + Texture", "smoke_test": args.smoke, "seed": args.seed, "config": vars(args) | {"manifest": str(args.manifest), "output_dir": str(args.output_dir)}, "manifest_sha256": integrity["manifest_sha256"], "git_commit": git_commit(), "python": sys.version, "torch": torch.__version__, "timm": timm.__version__, "device": str(device), "device_name": torch.cuda.get_device_name(0) if device.type == "cuda" else platform.processor(), "model_name": MODEL_NAME, "class_weights_train_only": weights.cpu().tolist(), "parameters": parameter_summary, "best_epoch": best_epoch, "best_validation_macro_f1": best_f1, "best_checkpoint_branch_weights": {"semantic": best_weights[0], "texture": best_weights[1]}, "epochs_completed": len(history), "duration_seconds": time.perf_counter() - started, "peak_rss_bytes": max(before_rss, getattr(process.memory_info(), "peak_wset", process.memory_info().rss)), "single_forward_seconds": forward_latency, "augmentation": [], "preprocessing": ["RGB", "ToTensor", "ImageNet normalization"], "history": history}
    (args.output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    if args.smoke: print(json.dumps(metadata, indent=2, default=str)); return 0
    # Test is instantiated only after validation-based checkpoint selection.
    test_set = ProtocolAReducedDataset(records, "test"); rows = predict(model, loader(test_set, args.batch_size, False, args.workers, args.seed), device)
    m3_metrics = json.loads(M3_METRICS.read_text(encoding="utf-8")); m3_rows = {r["sample_id"]: r for r in csv.DictReader(M3_PREDICTIONS.open(encoding="utf-8"))}
    metrics = classification_metrics([r[1] for r in rows], [r[2] for r in rows]); failures, padding, class_padding = [], {True: [0, 0], False: [0, 0]}, defaultdict(lambda: [0, 0])
    output_path = ROOT / "artifacts/metrics/m4_test_predictions.csv"; output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        fields = ["sample_id", "base_document_id", "true_class", "predicted_class", *[f"p_{c}" for c in CLASS_NAMES], "confidence", "padded", "crop_path", "comparison_to_m3", "semantic_norm", "texture_norm", "semantic_projected_norm", "texture_projected_norm", "combined_norm"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for index, target, prediction, probabilities, norms in rows:
            record = test_set.records[index]; sample_id = record["sample_id"]; m3 = m3_rows[sample_id]; error, padded_flag = target != prediction, bool(record["portrait_padding_applied"]); m3_error = m3["true_class"] != m3["predicted_class"]
            comparison = "PERSISTENT_FAILURE" if error and m3_error else "NEW_FAILURE" if error else "CORRECTED_M3_FAILURE" if m3_error else "CORRECT_BOTH"
            padding[padded_flag][0] += int(error); padding[padded_flag][1] += 1; class_padding[(record["mapped_label"], padded_flag)][0 if error else 1] += 1
            row = {"sample_id": sample_id, "base_document_id": record["base_document_id"], "true_class": CLASS_NAMES[target], "predicted_class": CLASS_NAMES[prediction], **{f"p_{c}": probabilities[i] for i, c in enumerate(CLASS_NAMES)}, "confidence": max(probabilities), "padded": padded_flag, "crop_path": record["portrait_crop_path"], "comparison_to_m3": comparison, **norms}; writer.writerow(row)
            if error: failures.append(row)
    metrics.update({"protocol": "Protocol A-Reduced", "best_epoch": best_epoch, "best_validation_macro_f1": best_f1, "learned_fusion_weights": {"semantic": best_weights[0], "texture": best_weights[1]}, "test_errors": len(failures), "padding_diagnostic": {str(k).lower(): {"errors": v[0], "count": v[1], "error_rate": v[0] / v[1]} for k, v in padding.items()}, "class_by_padding": {f"{k[0]}|padded={str(k[1]).lower()}": {"errors": v[0], "correct": v[1], "count": sum(v)} for k, v in class_padding.items()}, "failures": failures, "reproducibility": metadata})
    metrics_path = ROOT / "artifacts/metrics/m4_texture_metrics.json"; metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    delta = {"accuracy": metrics["accuracy"] - m3_metrics["accuracy"], "macro_f1": metrics["macro_f1"] - m3_metrics["macro_f1"], "per_class_f1": {c: metrics["per_class_f1"][i] - m3_metrics["per_class_f1"][i] for i, c in enumerate(CLASS_NAMES)}}
    comparison = {"m3": {"accuracy": m3_metrics["accuracy"], "macro_f1": m3_metrics["macro_f1"], "per_class_f1": dict(zip(CLASS_NAMES, m3_metrics["per_class_f1"], strict=True))}, "m4": {"accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1"], "per_class_f1": dict(zip(CLASS_NAMES, metrics["per_class_f1"], strict=True))}, "delta_m4_minus_m3": delta}
    (ROOT / "artifacts/metrics/m4_vs_m3.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8"); save_plots(history, metrics, failures, test_set)
    print(json.dumps({"metrics": metrics, "comparison": comparison}, indent=2, default=str)); return 0


if __name__ == "__main__": raise SystemExit(main())
