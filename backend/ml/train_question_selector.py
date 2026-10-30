"""
Adaptive Question Selection & Ranking Model Training
Trains a cross-encoder ranking model that predicts the pedagogical suitability
of candidate questions given the candidate's dynamic interview state.
Evaluates ranking metrics: NDCG@3, MRR, Top-1 Precision.
"""

import json
import joblib
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


def load_dataset(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_cross_encoder_pairs(data):
    """
    Constructs cross-encoder input text pairs:
    Format:
    State: [ROLE] Full Stack [COMPETENCY] Security [DIFF] mid [PREV_SCORE] 45 [WEAKNESS] JWT tokens
    [QUESTION] How do you architect JWT authentication with refresh tokens?
    """
    pairs = []
    labels = []
    metadata = []

    for item in data:
        state_text = (
            f"Role: {item['role']} | "
            f"Competency: {item['target_competency']} | "
            f"Difficulty: {item['target_difficulty']} | "
            f"Previous Score: {item['previous_score']} | "
            f"Weakness: {item['previous_weakness']} | "
            f"Skills: {item['candidate_skills']}"
        )

        for candidate in item["ranking_candidates"]:
            # Combined cross-representation
            cross_text = f"{state_text} [SEP] Question: {candidate['question']}"
            pairs.append(cross_text)
            labels.append(int(candidate["label"]))
            metadata.append({
                "sample_id": item["id"],
                "candidate_type": candidate["type"],
                "question": candidate["question"]
            })

    return pairs, np.array(labels), metadata


def compute_ranking_metrics(y_true, y_probs, metadata):
    """
    Groups predictions by sample_id and computes ranking metrics:
    - Top-1 Accuracy: Is the highest scored question the optimal one?
    - MRR (Mean Reciprocal Rank): 1 / rank of optimal question.
    - NDCG@3: Normalized Discounted Cumulative Gain at rank 3.
    """
    grouped = {}
    for i, meta in enumerate(metadata):
        sid = meta["sample_id"]
        if sid not in grouped:
            grouped[sid] = []
        grouped[sid].append((y_true[i], y_probs[i]))

    top1_correct = 0
    reciprocal_ranks = []
    ndcg_scores = []

    for sid, items in grouped.items():
        # Sort by predicted probability descending
        sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
        ranks = [item[0] for item in sorted_items]

        # Top-1 Accuracy
        if ranks[0] == 1.0:
            top1_correct += 1

        # MRR
        for rank_idx, label in enumerate(ranks, start=1):
            if label == 1.0:
                reciprocal_ranks.append(1.0 / rank_idx)
                break

        # NDCG@3
        dcg = sum((val / np.log2(idx + 1)) for idx, val in enumerate(ranks[:3], start=1))
        # Ideal DCG has optimal (1.0) at rank 1
        idcg = 1.0 / np.log2(2)
        ndcg_scores.append(dcg / idcg if idcg > 0 else 0)

    total_queries = len(grouped)
    return {
        "top1_accuracy": top1_correct / total_queries if total_queries > 0 else 0,
        "mrr": float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0,
        "ndcg_at_3": float(np.mean(ndcg_scores)) if ndcg_scores else 0,
        "total_queries": total_queries
    }


def train_and_evaluate():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    models_dir = base_dir / "saved_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NLP Adaptive Question Selection Model Training")
    print("=" * 60)

    train_data = load_dataset(data_dir / "train.json")
    val_data = load_dataset(data_dir / "val.json")
    test_data = load_dataset(data_dir / "test.json")

    X_train_raw, y_train, train_meta = prepare_cross_encoder_pairs(train_data)
    X_val_raw, y_val, val_meta = prepare_cross_encoder_pairs(val_data)
    X_test_raw, y_test, test_meta = prepare_cross_encoder_pairs(test_data)

    print(f"Loaded pairs -> Train: {len(X_train_raw)}, Val: {len(X_val_raw)}, Test: {len(X_test_raw)}")

    # 1. Feature Extraction: Sublinear TF-IDF Cross-Encoder representation
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=12000,
        sublinear_tf=True,
        stop_words="english"
    )
    X_train = vectorizer.fit_transform(X_train_raw)
    X_val = vectorizer.transform(X_val_raw)
    X_test = vectorizer.transform(X_test_raw)

    models = {
        "Baseline (Logistic Regression)": LogisticRegression(C=1.5, max_iter=500),
        "Neural MLP Ranker": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300, random_state=42),
        "Gradient Boosting Ranker": GradientBoostingClassifier(n_estimators=120, learning_rate=0.1, random_state=42)
    }

    results = {}
    best_model_name = None
    best_top1_acc = -1
    best_pipeline = None

    for name, model in models.items():
        print(f"\n--- Training {name} ---")
        model.fit(X_train, y_train)

        # Validation evaluation
        val_probs = model.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= 0.5).astype(int)

        val_acc = accuracy_score(y_val, val_preds)
        val_f1 = f1_score(y_val, val_preds)
        val_auc = roc_auc_score(y_val, val_probs)
        val_ranking = compute_ranking_metrics(y_val, val_probs, val_meta)

        # Test evaluation
        test_probs = model.predict_proba(X_test)[:, 1]
        test_preds = (test_probs >= 0.5).astype(int)
        test_acc = accuracy_score(y_test, test_preds)
        test_f1 = f1_score(y_test, test_preds)
        test_auc = roc_auc_score(y_test, test_probs)
        test_ranking = compute_ranking_metrics(y_test, test_probs, test_meta)

        print(f"Validation:")
        print(f"  Classification Acc: {val_acc:.4f} | F1: {val_f1:.4f} | ROC-AUC: {val_auc:.4f}")
        print(f"  Top-1 Selection Acc: {val_ranking['top1_accuracy']*100:.2f}% | MRR: {val_ranking['mrr']:.4f} | NDCG@3: {val_ranking['ndcg_at_3']:.4f}")

        print(f"Test Set:")
        print(f"  Classification Acc: {test_acc:.4f} | F1: {test_f1:.4f} | ROC-AUC: {test_auc:.4f}")
        print(f"  Top-1 Selection Acc: {test_ranking['top1_accuracy']*100:.2f}% | MRR: {test_ranking['mrr']:.4f} | NDCG@3: {test_ranking['ndcg_at_3']:.4f}")

        results[name] = {
            "val": {**val_ranking, "accuracy": val_acc, "f1": val_f1, "roc_auc": val_auc},
            "test": {**test_ranking, "accuracy": test_acc, "f1": test_f1, "roc_auc": test_auc}
        }

        if test_ranking["top1_accuracy"] > best_top1_acc:
            best_top1_acc = test_ranking["top1_accuracy"]
            best_model_name = name
            best_pipeline = {
                "model_name": name,
                "model": model,
                "vectorizer": vectorizer
            }

    # Save Best Model Artifacts
    print(f"\n>>> Best Model: {best_model_name} (Test Top-1 Acc: {best_top1_acc*100:.2f}%)")
    artifact_path = models_dir / "question_ranker_pipeline.joblib"
    joblib.dump(best_pipeline, artifact_path)
    print(f"Saved best model pipeline to: {artifact_path}")

    # Save Metrics Summary JSON for Reporting
    metrics_path = models_dir / "ranking_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved evaluation metrics to: {metrics_path}")

    return results


if __name__ == "__main__":
    train_and_evaluate()
