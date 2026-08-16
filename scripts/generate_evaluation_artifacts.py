from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_curve

from src.features.build_features import build_features
from src.training.threshold import threshold_table
from src.training.train import temporal_split


def confusion_svg(metrics: dict, output: Path):
    values = [[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]]
    labels = [["TN", "FP"], ["FN", "TP"]]
    maximum = max(max(row) for row in values) or 1
    cells = []
    for r in range(2):
        for c in range(2):
            value = values[r][c]; shade = 245 - int(150 * value / maximum)
            x, y = 170 + c * 190, 90 + r * 130
            cells.append(f'<rect x="{x}" y="{y}" width="180" height="120" rx="8" fill="rgb({shade},{shade+5},255)"/>')
            cells.append(f'<text x="{x+90}" y="{y+48}" text-anchor="middle" font-size="20">{labels[r][c]}</text>')
            cells.append(f'<text x="{x+90}" y="{y+82}" text-anchor="middle" font-size="26" font-weight="bold">{value:,}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="390">
<rect width="100%" height="100%" fill="white"/><text x="280" y="38" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold">Test Confusion Matrix</text>
<text x="360" y="375" text-anchor="middle" font-family="Arial" font-size="16">Predicted class</text><text x="24" y="230" transform="rotate(-90 24 230)" text-anchor="middle" font-family="Arial" font-size="16">Actual class</text>
<g font-family="Arial">{''.join(cells)}</g></svg>'''
    output.write_text(svg, encoding="utf-8")


def line_svg(series, output: Path, title: str, x_label: str, y_label: str):
    width, height = 760, 430; left, top, plot_w, plot_h = 75, 55, 640, 310
    colors = ["#2563eb", "#dc2626", "#059669"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{title}</text>',
             f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#111"/><line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#111"/>']
    all_x = np.concatenate([np.asarray(x) for _,x,_ in series]); all_y = np.concatenate([np.asarray(y) for _,_,y in series])
    xmin,xmax=float(all_x.min()),float(all_x.max()); ymin,ymax=float(all_y.min()),float(all_y.max()); ymax=max(ymax, ymin+1e-9)
    for i,(label,x,y) in enumerate(series):
        pts=[]
        for xv,yv in zip(x,y):
            px=left+(float(xv)-xmin)/(xmax-xmin or 1)*plot_w; py=top+plot_h-(float(yv)-ymin)/(ymax-ymin)*plot_h; pts.append(f"{px:.1f},{py:.1f}")
        parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colors[i]}" stroke-width="2"/><text x="{left+15+i*190}" y="{height-12}" font-family="Arial" font-size="14" fill="{colors[i]}">{label}</text>')
    parts += [f'<text x="{left+plot_w/2}" y="{height-35}" text-anchor="middle" font-family="Arial" font-size="14">{x_label}</text>', f'<text x="18" y="{top+plot_h/2}" transform="rotate(-90 18 {top+plot_h/2})" text-anchor="middle" font-family="Arial" font-size="14">{y_label}</text></svg>']
    output.write_text("".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True); parser.add_argument("--model", required=True)
    parser.add_argument("--metadata", required=True); parser.add_argument("--output-dir", default="output/evaluation")
    args = parser.parse_args(); out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8")); model = joblib.load(args.model)
    dtypes = {"step":"int16","type":"category","amount":"float32","oldbalanceOrg":"float32","newbalanceOrig":"float32","oldbalanceDest":"float32","newbalanceDest":"float32","isFraud":"int8"}
    frame = pd.read_csv(args.input, usecols=list(dtypes), dtype=dtypes)
    _, validation, _ = temporal_split(frame)
    scores = model.predict_proba(build_features(validation)[metadata["feature_list"]])[:, 1]
    table = threshold_table(validation.isFraud, scores, amounts=validation.amount)
    table.to_csv(out / "threshold_analysis.csv", index=False)
    confusion_svg(metadata["test_metrics"], out / "confusion_matrix_test.svg")
    precision, recall, _ = precision_recall_curve(validation.isFraud, scores)
    line_svg([("Precision-Recall", recall, precision)], out / "precision_recall_validation.svg", "Validation Precision-Recall Curve", "Recall", "Precision")
    line_svg([("Precision",table.threshold,table.precision),("Recall",table.threshold,table.recall),("F2",table.threshold,table.f2)], out / "threshold_metrics.svg", "Threshold Metrics", "Threshold", "Metric")
    line_svg([("Alerts / 1,000",table.threshold,table.alerts_per_1000)], out / "threshold_alert_volume.svg", "Threshold vs Alert Volume", "Threshold", "Alerts per 1,000")
    print(f"Wrote evaluation artifacts to {out}")


if __name__ == "__main__": main()
