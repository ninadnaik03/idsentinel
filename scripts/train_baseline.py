"""Train/evaluate the M3 semantic ConvNeXt baseline on Protocol A-Reduced."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from collections import Counter
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
from src.models.backbone import MODEL_NAME, SemanticConvNeXtTiny
from src.training.metrics import classification_metrics


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def optimizer_for(model: SemanticConvNeXtTiny):
    return torch.optim.AdamW([
        {"params": list(model.backbone_parameters()), "lr": 5e-7, "name": "trainable_backbone"},
        {"params": list(model.classifier_parameters()), "lr": 5e-6, "name": "classifier"},
    ], weight_decay=0.01)


def loader(dataset, batch_size, shuffle, workers, seed):
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=workers, generator=generator, pin_memory=torch.cuda.is_available())


def fit_cuda_batch(model, requested: int) -> int:
    """Probe backward memory and reduce only physical batch size on CUDA OOM."""
    for candidate in [size for size in (requested, 8, 4, 2, 1) if size <= requested]:
        try:
            model.zero_grad(set_to_none=True)
            dummy = torch.zeros(candidate, 3, 384, 384, device="cuda")
            model(dummy).sum().backward()
            model.zero_grad(set_to_none=True); del dummy; torch.cuda.empty_cache()
            return candidate
        except torch.OutOfMemoryError:
            model.zero_grad(set_to_none=True); torch.cuda.empty_cache()
    raise RuntimeError("ConvNeXt-Tiny 384x384 backward pass does not fit at CUDA batch size 1")


def run_epoch(model, data_loader, criterion, device, optimizer=None, accumulation=1, scaler=None):
    training = optimizer is not None
    model.train(training)
    targets, predictions, losses = [], [], []
    if training: optimizer.zero_grad(set_to_none=True)
    for step, (images, labels, _) in enumerate(data_loader):
        images, labels = images.to(device), labels.to(device)
        with torch.autocast(device_type=device.type, enabled=scaler is not None):
            logits = model(images); loss = criterion(logits, labels)
        if training:
            scaled = loss / accumulation
            if scaler is not None: scaler.scale(scaled).backward()
            else: scaled.backward()
            if (step + 1) % accumulation == 0 or step + 1 == len(data_loader):
                if scaler is not None: scaler.step(optimizer); scaler.update()
                else: optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach())); targets.extend(labels.cpu().tolist()); predictions.extend(logits.argmax(1).detach().cpu().tolist())
    metrics = classification_metrics(targets, predictions)
    metrics["loss"] = float(np.mean(losses))
    return metrics


@torch.no_grad()
def predict(model, data_loader, device):
    model.eval(); output = []
    for images, labels, indices in data_loader:
        probabilities = model(images.to(device)).softmax(1).cpu()
        for target, index, probability in zip(labels.tolist(), indices.tolist(), probabilities.tolist(), strict=True):
            output.append((index, target, int(np.argmax(probability)), probability))
    return output


def save_curves(history, path: Path):
    epochs = [row["epoch"] for row in history]
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(epochs, [row["train"]["loss"] for row in history], label="train"); axes[0].plot(epochs, [row["validation"]["loss"] for row in history], label="validation")
    axes[0].set_title("Loss"); axes[0].legend()
    axes[1].plot(epochs, [row["train"]["macro_f1"] for row in history], label="train"); axes[1].plot(epochs, [row["validation"]["macro_f1"] for row in history], label="validation")
    axes[1].set_title("Macro F1"); axes[1].legend(); figure.tight_layout(); path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)


def save_confusion(matrix, path: Path):
    figure, axis = plt.subplots(figsize=(5, 4)); image = axis.imshow(matrix, cmap="Blues")
    for row in range(3):
        for col in range(3): axis.text(col, row, matrix[row][col], ha="center", va="center")
    axis.set_xticks(range(3), CLASS_NAMES, rotation=25); axis.set_yticks(range(3), CLASS_NAMES); axis.set_xlabel("Predicted"); axis.set_ylabel("True"); figure.colorbar(image); figure.tight_layout(); path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)


def save_failure_grid(failures, path: Path):
    if not failures: return
    from PIL import Image
    columns, rows = 4, (len(failures) + 3) // 4
    figure, axes = plt.subplots(rows, columns, figsize=(columns * 3, rows * 3.4), squeeze=False)
    for axis, failure in zip(axes.flat, failures):
        axis.imshow(Image.open(failure["crop_path"]).convert("RGB")); axis.set_title(f"{failure['true_class']} → {failure['predicted_class']}\npad={failure['padded']}", fontsize=8); axis.axis("off")
    for axis in axes.flat[len(failures):]: axis.axis("off")
    figure.tight_layout(); path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=150); plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "artifacts/data/dlc2021_protocol_a_reduced_manifest.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/m3")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--batch-size", type=int, default=8); parser.add_argument("--accumulation", type=int, default=4); parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=250); parser.add_argument("--seed", type=int, default=20250813); parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--smoke", action="store_true"); parser.add_argument("--no-pretrained", action="store_true")
    args = parser.parse_args(); seed_everything(args.seed)
    records, integrity = load_and_validate_manifest(args.manifest)
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
    if args.smoke:
        args.device, args.batch_size, args.accumulation, args.workers, args.epochs = "cpu", 1, 1, 0, 1; device = torch.device("cpu")
        args.output_dir = ROOT / "artifacts/smoke/m3"
    train_set = ProtocolAReducedDataset(records, "train", training=True); validation_set = ProtocolAReducedDataset(records, "validation")
    if args.smoke:
        train_set = Subset(train_set, [0]); validation_set = Subset(validation_set, [0, 15, 30])
    started = time.perf_counter(); before_rss = psutil.Process().memory_info().rss
    model = SemanticConvNeXtTiny(pretrained=not args.no_pretrained).to(device); model.assert_freeze_policy(); parameter_summary = model.parameter_summary()
    if device.type == "cuda":
        args.batch_size = fit_cuda_batch(model, args.batch_size)
        args.accumulation = max(args.accumulation, int(np.ceil(32 / args.batch_size)))
    train_loader = loader(train_set, args.batch_size, True, args.workers, args.seed); validation_loader = loader(validation_set, args.batch_size, False, args.workers, args.seed)
    weights = torch.tensor(training_class_weights(records), dtype=torch.float32, device=device); criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = optimizer_for(model); scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", patience=5, factor=0.5)
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None
    args.output_dir.mkdir(parents=True, exist_ok=True); checkpoint = args.output_dir / "best_baseline.pt"
    history, best_f1, best_epoch, stale = [], -1.0, 0, 0
    forward_started = time.perf_counter()
    with torch.no_grad(): model(next(iter(validation_loader))[0][:1].to(device))
    forward_latency = time.perf_counter() - forward_started
    for epoch in range(1, args.epochs + 1):
        train_metrics = run_epoch(model, train_loader, criterion, device, optimizer, args.accumulation, scaler)
        validation_metrics = run_epoch(model, validation_loader, criterion, device)
        scheduler.step(validation_metrics["macro_f1"]); history.append({"epoch": epoch, "train": train_metrics, "validation": validation_metrics, "learning_rates": [group["lr"] for group in optimizer.param_groups]})
        if validation_metrics["macro_f1"] > best_f1:
            best_f1, best_epoch, stale = validation_metrics["macro_f1"], epoch, 0
            torch.save({"model": model.state_dict(), "epoch": epoch, "validation_macro_f1": best_f1, "manifest_sha256": integrity["manifest_sha256"], "class_names": CLASS_NAMES}, checkpoint)
        else: stale += 1
        if stale >= args.patience: break
    loaded = torch.load(checkpoint, map_location=device, weights_only=True); model.load_state_dict(loaded["model"])
    reproducibility = {
        "protocol": "Protocol A-Reduced", "smoke_test": args.smoke, "seed": args.seed, "config": vars(args) | {"manifest": str(args.manifest), "output_dir": str(args.output_dir)},
        "manifest_sha256": integrity["manifest_sha256"], "git_commit": git_commit(), "python": sys.version, "torch": torch.__version__, "timm": timm.__version__,
        "device": str(device), "device_name": torch.cuda.get_device_name(0) if device.type == "cuda" else platform.processor(), "model_name": MODEL_NAME,
        "class_weights_train_only": weights.cpu().tolist(), "parameters": parameter_summary, "best_epoch": best_epoch, "best_validation_macro_f1": best_f1,
        "epochs_completed": len(history), "duration_seconds": time.perf_counter() - started, "peak_rss_bytes": max(before_rss, getattr(psutil.Process().memory_info(), "peak_wset", psutil.Process().memory_info().rss)), "single_forward_seconds": forward_latency,
        "augmentation": [], "preprocessing": ["RGB", "ToTensor", "ImageNet normalization"], "history": history,
    }
    (args.output_dir / "run_metadata.json").write_text(json.dumps(reproducibility, indent=2, default=str), encoding="utf-8")
    save_curves(history, args.output_dir / "training_curves.png")
    if args.smoke:
        print(json.dumps(reproducibility, indent=2, default=str)); return 0
    # Test is instantiated and evaluated only after the best validation checkpoint is loaded.
    test_set = ProtocolAReducedDataset(records, "test"); test_loader = loader(test_set, args.batch_size, False, args.workers, args.seed)
    rows = predict(model, test_loader, device); metrics = classification_metrics([row[1] for row in rows], [row[2] for row in rows])
    predictions_path = ROOT / "artifacts/metrics/m3_test_predictions.csv"; predictions_path.parent.mkdir(parents=True, exist_ok=True)
    failures = []; padded = {True: [0, 0], False: [0, 0]}; class_padding = Counter()
    with predictions_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["sample_id", "base_document_id", "true_class", "predicted_class", *[f"p_{label}" for label in CLASS_NAMES], "confidence", "padded", "detector", "crop_path"])
        for index, target, prediction, probabilities in rows:
            record = test_set.records[index]; padded_flag = bool(record["portrait_padding_applied"]); error = target != prediction
            padded[padded_flag][0] += int(error); padded[padded_flag][1] += 1; class_padding[(record["mapped_label"], padded_flag, error)] += 1
            output = [record["sample_id"], record["base_document_id"], CLASS_NAMES[target], CLASS_NAMES[prediction], *probabilities, max(probabilities), padded_flag, record["portrait_detector"], record["portrait_crop_path"]]; writer.writerow(output)
            if error: failures.append({"sample_id": record["sample_id"], "base_document_id": record["base_document_id"], "true_class": CLASS_NAMES[target], "predicted_class": CLASS_NAMES[prediction], "probabilities": dict(zip(CLASS_NAMES, probabilities)), "confidence": max(probabilities), "padded": padded_flag, "detector_stage": record["portrait_detector"], "capture_id": record["capture_id"], "document_type": record["document_type"], "source_member": record["source_member"], "crop_path": record["portrait_crop_path"]})
    metrics.update({"protocol": "Protocol A-Reduced", "best_epoch": best_epoch, "best_validation_macro_f1": best_f1, "test_errors": len(failures), "padding_diagnostic": {str(key).lower(): {"errors": value[0], "count": value[1], "error_rate": value[0] / value[1] if value[1] else None} for key, value in padded.items()}, "class_stratified_padding_errors": {str(key): value for key, value in class_padding.items()}, "failures": failures, "reproducibility": reproducibility})
    metrics_path = ROOT / "artifacts/metrics/m3_baseline_metrics.json"; metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    save_confusion(metrics["confusion_matrix"], ROOT / "artifacts/plots/m3_confusion_matrix.png"); save_curves(history, ROOT / "artifacts/plots/m3_training_curves.png")
    save_failure_grid(failures, ROOT / "artifacts/plots/m3_failures.png")
    report = ["# M3 Failure Analysis", "", "Protocol A-Reduced; observed test errors only. Detector metadata is analysis-only.", "", f"Test errors: {len(failures)}", ""]
    for failure in failures:
        report.extend([f"## {failure['sample_id']}", "", f"- Observed: {failure['true_class']} → {failure['predicted_class']}; confidence {failure['confidence']:.4f}; padded={failure['padded']}; detector={failure['detector_stage']}.", f"- Metadata: document type `{failure['document_type']}`, capture `{failure['capture_id']}`.", "- Possible explanation: requires visual review; no causal explanation is inferred automatically.", ""])
    failure_report_path = ROOT / "docs/M3_FAILURE_ANALYSIS.md"; failure_report_path.parent.mkdir(parents=True, exist_ok=True); failure_report_path.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(metrics, indent=2, default=str)); return 0


if __name__ == "__main__": raise SystemExit(main())
