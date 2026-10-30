# Academic Model Evaluation & Benchmarking Report
## Task: Dynamic Adaptive Question Selection & Ranking

### 1. Test Set Performance Comparison (Ablation Study)

| Model Architecture | Top-1 Selection Acc | MRR | NDCG@3 | Binary Classif. Acc | Macro F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| **Baseline (Logistic Regression)** | 63.33% | 0.7903 | 0.8439 | 76.39% | 0.4970 | 0.8093 |
| **Neural MLP Ranker** | 100.00% | 1.0000 | 1.0000 | 99.17% | 0.9876 | 0.9997 |
| **Gradient Boosting Ranker** | 90.00% | 0.9417 | 0.9565 | 87.22% | 0.7629 | 0.9291 |

### 2. Validation Set Performance

| Model Architecture | Top-1 Selection Acc | MRR | NDCG@3 | Binary Classif. Acc | Macro F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| **Baseline (Logistic Regression)** | 70.00% | 0.8361 | 0.8784 | 78.06% | 0.5269 | 0.8660 |
| **Neural MLP Ranker** | 100.00% | 1.0000 | 1.0000 | 100.00% | 1.0000 | 1.0000 |
| **Gradient Boosting Ranker** | 88.33% | 0.9347 | 0.9515 | 87.50% | 0.7716 | 0.9500 |

### 3. Metric Definitions for Academic Reporting
- **Top-1 Selection Accuracy**: Percentage of test queries where the highest-ranked question was the pedagogically optimal question.
- **MRR (Mean Reciprocal Rank)**: $\frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$, measuring how high the optimal question is placed in the rank ordering.
- **NDCG@3 (Normalized Discounted Cumulative Gain)**: Evaluates graded relevance discounted logarithmically by rank position up to rank 3.
- **ROC-AUC**: Area under the Receiver Operating Characteristic curve measuring discrimination threshold separability.