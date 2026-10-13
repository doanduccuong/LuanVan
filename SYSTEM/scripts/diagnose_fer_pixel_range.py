"""Measure fixed pixel-range ablations on FER PublicTest, with frozen weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def summarize(labels: np.ndarray, predictions: np.ndarray) -> dict:
    matrix = np.zeros((7,7), dtype=np.int64)
    np.add.at(matrix, (labels, predictions), 1)
    tp = np.diag(matrix).astype(float)
    denominators = matrix.sum(axis=0) + matrix.sum(axis=1)
    f1 = np.divide(2*tp, denominators, out=np.zeros(7), where=denominators>0)
    return {"accuracy": float((labels==predictions).mean()),
            "correct": int((labels==predictions).sum()), "count": len(labels),
            "macro_f1": float(f1.mean()), "confusion_matrix": matrix.tolist()}


def main(data: Path, output: Path, original: Path, finetuned: Path) -> None:
    from deepface import DeepFace

    client = DeepFace.build_model(model_name="Emotion", task="facial_attribute")
    bundle = np.load(data, allow_pickle=False)
    assert str(bundle["split"])=="PublicTest"
    images, labels = bundle["images"], bundle["labels"]
    assert images.shape==(3589,48,48)
    results = {"split": "PublicTest", "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
               "scope": "Read-only diagnosis; no training or checkpoint selection"}
    for name, weights in (("original",original),("finetuned",finetuned)):
        client.model.load_weights(str(weights))
        results[name]={"model_sha256":hashlib.sha256(weights.read_bytes()).hexdigest()}
        for scale_name, scale in (("0_to_255",1.0),("0_to_1",1/255)):
            scores=[]
            for start in range(0,len(images),128):
                tensor=images[start:start+128,...,None].astype(np.float32)*scale
                scores.append(np.asarray(client.model(tensor,training=False).numpy()))
            metrics=summarize(labels,np.concatenate(scores).argmax(axis=1))
            results[name][scale_name]=metrics
            print(f"{name} {scale_name}: accuracy={metrics['accuracy']:.6f} "
                  f"macro_f1={metrics['macro_f1']:.6f}",flush=True)
    output.write_text(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--finetuned",type=Path,required=True)
    args=parser.parse_args()
    main(args.data,args.output,args.original,args.finetuned)
