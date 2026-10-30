"""
Comprehensive NLP Project Model Evaluator & Metrics Reporter
Generates academic benchmarking metrics, ablation comparisons,
and formatted tables for the NLP course project report.
"""

import json
from pathlib import Path


def generate_evaluation_report():
    base_dir = Path(__file__).resolve().parent
    metrics_file = base_dir / "saved_models" / "ranking_metrics.json"

    if not metrics_file.exists():
        print(f"Error: {metrics_file} not found. Please run train_question_selector.py first.")
        return

    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    report_lines = []
    report_lines.append("# Academic Model Evaluation & Benchmarking Report")
    report_lines.append("## Task: Dynamic Adaptive Question Selection & Ranking\n")
    report_lines.append("### 1. Test Set Performance Comparison (Ablation Study)\n")
    report_lines.append(
        "| Model Architecture | Top-1 Selection Acc | MRR | NDCG@3 | Binary Classif. Acc | Macro F1 | ROC-AUC |"
    )
    report_lines.append(
        "|---|---|---|---|---|---|---|"
    )

    for model_name, data in metrics.items():
        test_m = data["test"]
        top1 = f"{test_m['top1_accuracy'] * 100:.2f}%"
        mrr = f"{test_m['mrr']:.4f}"
        ndcg = f"{test_m['ndcg_at_3']:.4f}"
        acc = f"{test_m['accuracy'] * 100:.2f}%"
        f1 = f"{test_m['f1']:.4f}"
        auc = f"{test_m['roc_auc']:.4f}"
        report_lines.append(f"| **{model_name}** | {top1} | {mrr} | {ndcg} | {acc} | {f1} | {auc} |")

    report_lines.append("\n### 2. Validation Set Performance\n")
    report_lines.append(
        "| Model Architecture | Top-1 Selection Acc | MRR | NDCG@3 | Binary Classif. Acc | Macro F1 | ROC-AUC |"
    )
    report_lines.append(
        "|---|---|---|---|---|---|---|"
    )
    for model_name, data in metrics.items():
        val_m = data["val"]
        top1 = f"{val_m['top1_accuracy'] * 100:.2f}%"
        mrr = f"{val_m['mrr']:.4f}"
        ndcg = f"{val_m['ndcg_at_3']:.4f}"
        acc = f"{val_m['accuracy'] * 100:.2f}%"
        f1 = f"{val_m['f1']:.4f}"
        auc = f"{val_m['roc_auc']:.4f}"
        report_lines.append(f"| **{model_name}** | {top1} | {mrr} | {ndcg} | {acc} | {f1} | {auc} |")

    report_lines.append("\n### 3. Metric Definitions for Academic Reporting")
    report_lines.append("- **Top-1 Selection Accuracy**: Percentage of test queries where the highest-ranked question was the pedagogically optimal question.")
    report_lines.append("- **MRR (Mean Reciprocal Rank)**: $\\frac{1}{|Q|} \\sum_{i=1}^{|Q|} \\frac{1}{\\text{rank}_i}$, measuring how high the optimal question is placed in the rank ordering.")
    report_lines.append("- **NDCG@3 (Normalized Discounted Cumulative Gain)**: Evaluates graded relevance discounted logarithmically by rank position up to rank 3.")
    report_lines.append("- **ROC-AUC**: Area under the Receiver Operating Characteristic curve measuring discrimination threshold separability.")

    report_content = "\n".join(report_lines)
    print(report_content)

    report_out_path = base_dir / "MODEL_BENCHMARK_REPORT.md"
    with open(report_out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\nReport saved to: {report_out_path}")


if __name__ == "__main__":
    generate_evaluation_report()
