"""Dependency-light multiclass metrics."""

from __future__ import annotations

import numpy as np


def classification_metrics(targets, predictions, num_classes: int = 3) -> dict:
    matrix = np.zeros((num_classes, num_classes), dtype=int)
    for target, prediction in zip(targets, predictions, strict=True):
        matrix[int(target), int(prediction)] += 1
    precision, recall, f1 = [], [], []
    for index in range(num_classes):
        tp = matrix[index, index]
        p = tp / matrix[:, index].sum() if matrix[:, index].sum() else 0.0
        r = tp / matrix[index].sum() if matrix[index].sum() else 0.0
        precision.append(p); recall.append(r); f1.append(2 * p * r / (p + r) if p + r else 0.0)
    return {
        "accuracy": float(np.trace(matrix) / matrix.sum()) if matrix.sum() else 0.0,
        "macro_precision": float(np.mean(precision)), "macro_recall": float(np.mean(recall)), "macro_f1": float(np.mean(f1)),
        "per_class_precision": precision, "per_class_recall": recall, "per_class_f1": f1, "confusion_matrix": matrix.tolist(),
    }
