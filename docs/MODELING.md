# Modeling

This covers Phase 3 for both tracks. Every number in this document came from running `src/model/track_a_model.py` and `src/model/track_b_model.py` against the cleaned data. Nothing here is estimated.

## 1. Modeling objectives

The goal is a credible, reproducible modeling layer, not a maximized accuracy score. Emphasis is on defensible feature engineering, leakage prevention, appropriate model selection given class imbalance, and honest evaluation, in that order. This is an analytical prototype, not a system proposed for deployment at any institution.

## 2. Targets

- Track A: `churn` (0 = retained, 1 = churned), from `data/processed/churn_clean.csv`. 18.53% positive.
- Track B: `y` (yes/no, mapped to 1/0), from `data/processed/bank_additional_clean.csv`. 11.27% positive.

## 3. Feature selection

### Track A
Numeric: `vintage`, `age`, `dependents`, `customer_nw_category`, `current_balance`, `previous_month_end_balance`, `average_monthly_balance_prevQ`, `average_monthly_balance_prevQ2`, `current_month_credit`, `previous_month_credit`, `current_month_debit`, `previous_month_debit`, `current_month_balance`, `previous_month_balance`, and an engineered `days_since_last_transaction`.
Binary: `age_under_18_flag` (carried over from cleaning), and an engineered `last_transaction_missing_flag`.
Categorical: `gender`, `occupation`.
Excluded: `customer_id` (identifier), `city` and `branch_code` (high-cardinality codes, DATA_AUDIT.md), and the raw `last_transaction` date, which is converted into the two engineered fields above rather than used directly.

### Track B
Taken directly from `src/data/feature_config.py: MODEL_READY_FEATURES`, which already excludes `duration`. Numeric: `age`, `campaign`, `days_since_previous_contact`, `previous`, and the five macroeconomic indicators. Binary: `previous_contact_flag`. Categorical: `job`, `marital`, `education`, `default`, `housing`, `loan`, `contact`, `month`, `day_of_week`, `poutcome`. `track_b_model.py` asserts at runtime that this feature set matches `feature_config.py` and that `duration` is absent, so the exclusion cannot silently drift.

## 4. Leakage prevention

Both scripts import shared preprocessing only, never a fitted transformer computed on the full dataset. `duration` is never read from the CSV in `track_b_model.py`, not filtered out after loading. Track A's two engineered features from `last_transaction` were checked specifically for a leakage pattern: `last_transaction_missing_flag` does not appear in the top 10 features by Random Forest importance or permutation importance for either model, and `days_since_last_transaction` ranks well behind the balance-related features. Given the counterintuitive result already found in STATISTICAL_ANALYSIS.md T4 (missing transaction date associated with lower, not higher, churn), this was checked rather than assumed safe. Neither engineered feature dominates the model, which argues against it being a disguised leakage source, though it remains worth a second look if this model is extended.

## 5. Train/test methodology

80/20 train/test split, stratified on the target, `random_state = 42` for both tracks. The test set was not touched until final evaluation. Model comparison during development used 5-fold stratified cross-validation on the training set only, scored on average precision (equivalent to PR-AUC), so the test set numbers reported below were computed exactly once per model.

## 6. Preprocessing

A single `ColumnTransformer` per track, fit only on the training fold in every case (inside cross-validation folds and again on the full training set for final test evaluation), never on the full dataset before splitting. Numeric features: median imputation, then standardization. Categorical features: most-frequent imputation, then one-hot encoding with unknown categories at test time ignored rather than raising an error.

## 7. Models tested

Logistic Regression, Decision Tree (max_depth = 6), Random Forest (300 trees, max_depth = 10), all with `class_weight="balanced"` and `random_state = 42`. No hyperparameter search was run; depth limits were chosen to keep the tree and forest reasonably interpretable and to reduce overfitting risk given the class imbalance, not tuned against the test set.

## 8. Class imbalance strategy

`class_weight="balanced"` was used for all three models on both tracks, rather than oversampling or SMOTE. This was the simplest approach that directly addresses the imbalance without synthesizing data, consistent with preferring the simplest defensible method. Evaluation relies on PR-AUC, precision, recall, and F1 rather than accuracy, and a full threshold sweep is reported below rather than assuming 0.50 is appropriate.

## 9. Evaluation metrics

Reported at the default 0.50 threshold for comparability across models, plus ROC-AUC and PR-AUC, which are threshold-independent.

### Track A test set (n = 5,677, stratified from 28,382 total; train n = 22,705)

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 | Sensitivity | Specificity | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.7398 | 0.4451 | 0.3388 | 0.6635 | 0.4486 | 0.6635 | 0.7055 | 0.6845 |
| Decision Tree | 0.7957 | 0.5541 | 0.4708 | 0.6587 | 0.5491 | 0.6587 | 0.8316 | 0.7452 |
| Random Forest | 0.8422 | 0.6214 | 0.5707 | 0.6141 | 0.5916 | 0.6141 | 0.8949 | 0.7545 |

5-fold CV average precision on the training set: Logistic Regression 0.4371 (SD 0.0217), Decision Tree 0.5494 (SD 0.0138), Random Forest 0.6038 (SD 0.0172). The ranking matches the held-out test set, which is a reasonable stability check given this is a single train/test split.

### Track B test set (n = 8,236, stratified from 41,176 total; train n = 32,940)

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 | Sensitivity | Specificity | Balanced Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8001 | 0.4459 | 0.3593 | 0.6455 | 0.4617 | 0.6455 | 0.8539 | 0.7497 |
| Decision Tree | 0.7982 | 0.4487 | 0.3989 | 0.6293 | 0.4883 | 0.6293 | 0.8796 | 0.7544 |
| Random Forest | 0.8128 | 0.4766 | 0.4194 | 0.6304 | 0.5037 | 0.6304 | 0.8892 | 0.7598 |

5-fold CV average precision on the training set: Logistic Regression 0.4459 (SD 0.0126), Decision Tree 0.4137 (SD 0.0114), Random Forest 0.4584 (SD 0.0156).

Confusion matrices at the 0.50 threshold are in the threshold analysis files (`data/model_outputs/track_a_threshold_analysis.csv`, `track_b_threshold_analysis.csv`), which include the full precision/recall/F1/sensitivity/specificity/balanced accuracy sweep, not just the 0.50 row.

## 10. Model comparison

Random Forest has the highest PR-AUC on both tracks and the highest ROC-AUC on both tracks. It is not simply the highest-accuracy option picked without review: PR-AUC (not accuracy) was the selection criterion specifically because both targets are imbalanced, and its ranking is consistent between cross-validation and the held-out test set on both tracks, which is a check against the result being a fluke of one particular split.

## 11. Final model selection

**Random Forest, both tracks.** Reasoning: highest PR-AUC and ROC-AUC on both tracks, consistent with cross-validation, and it still supports feature importance and permutation importance for interpretability, so the interpretability requirement does not force a fallback to logistic regression. Decision Tree is reported alongside it as the more directly readable alternative (a single tree can be described in plain business language, a forest cannot), for anyone who needs a simpler story than "an ensemble said so."

## 12. Feature importance

### Track A (Random Forest, top 5 by permutation importance on the test set)
1. `current_balance` (0.310)
2. `average_monthly_balance_prevQ` (0.043)
3. `current_month_debit` (0.042)
4. `current_month_balance` (0.030)
5. `previous_month_balance` (0.023)

Balance-related features dominate by a wide margin, consistent with STATISTICAL_ANALYSIS.md T1 (current balance had the largest effect size found anywhere in Track A). Logistic regression coefficients point the same direction: `current_balance` has the largest-magnitude coefficient (-5.23, negative because higher balance is associated with lower churn given the encoding). Full lists in `data/model_outputs/track_a_rf_importance.csv`, `track_a_logreg_coefficients.csv`, and `track_a_permutation_importance.csv`.

### Track B (Random Forest, top 5 by permutation importance on the test set)
1. `euribor3m` (0.061)
2. `nr.employed` (0.052)
3. `contact` (0.035)
4. `emp.var.rate` (0.032)
5. `poutcome` (0.030)

The macroeconomic indicators dominate, more than any client-level attribute. This is consistent with the underlying business reality: term deposit subscription responds to prevailing interest rates and employment conditions, not only to who is called. `previous_contact_flag` (0.020) and demographic attributes rank below the macro variables. Full lists in `data/model_outputs/track_b_rf_importance.csv`, `track_b_logreg_coefficients.csv`, and `track_b_permutation_importance.csv`.

None of this should be read as causal. These are features associated with, and predictive of, the outcome within this dataset. A high `current_balance` is associated with lower churn risk in this model; it did not cause a customer to stay.

## 13. Threshold analysis

Full sweep from 0.10 to 0.90 in `data/model_outputs/track_a_threshold_analysis.csv` and `track_b_threshold_analysis.csv`. 0.50 is not assumed to be optimal for either track; it is reported because it is the standard reference point for comparing models, not because it is recommended for use.

**Track A.** At 0.50: precision 0.571, recall 0.614. At 0.35: precision 0.413, recall 0.799, sensitivity nearly doubles for a smaller drop in precision. For a retention-monitoring use case, where the cost of a missed at-risk customer (a lost account) is plausibly higher than the cost of an unnecessary check-in call, a lower threshold around 0.35 trades roughly 16 points of precision for 19 points of recall. This is presented as an analytical option, not a claim about what threshold Standard Chartered or any institution would actually use; the right threshold depends on the actual cost of a missed churn versus the actual cost of an unnecessary outreach, which is not known from this dataset.

**Track B.** At 0.50: precision 0.419, recall 0.630. F1 peaks near threshold 0.60 (precision 0.470, recall 0.588, F1 0.523), but campaign outreach by phone is typically low-cost relative to the value of a converted term deposit, which would argue for a lower threshold that keeps recall higher, for example 0.40 (precision 0.313, recall 0.706). As with Track A, the actual right answer depends on a real cost-per-contact and value-per-conversion figure that this dataset does not provide.

## 14. Business interpretation

### Track A
This model could plausibly support: flagging customers with elevated predicted churn risk for a relationship manager to review, prioritizing which accounts get proactive outreach when capacity is limited, and improving customer-level risk reporting alongside the existing segmentation from Phase 2. Segment 2 from SEGMENTATION_DECISION.md ("High Activity, High Churn") and this model's reliance on balance and activity features point in the same direction: engagement alone does not predict retention, and balance trajectory is a more useful signal than raw demographic attributes. This is a prototype for analytical review, not a system that has been validated for or proposed for production deployment.

### Track B
This model could plausibly support: ranking which clients in a contact list are more likely to respond, informing which months or macroeconomic conditions are more favorable for running a campaign, and prioritizing recontact of clients with a prior successful outcome, which the underlying statistics (STATISTICAL_ANALYSIS.md T5, T6) already identified as the single strongest lever available. The model itself adds a macroeconomic dimension the earlier statistical analysis touched only in passing: predicted adoption is more sensitive to the interest-rate and employment environment than to any individual client attribute in this dataset. Again, this is an analytical prototype, not a system that has been proposed for actual campaign deployment.

## 15. Limitations

- Track A and Track B remain unjoined, as established in Phase 1 and Phase 2; the two models are entirely independent and cannot be combined into a single customer risk score.
- No hyperparameter search was performed. Reported metrics reflect reasonable default configurations, not a ceiling on what either model type could achieve.
- Both datasets are static snapshots. Neither model has been validated on a genuinely out-of-time sample, since no true calendar date is available for Track B (documented in DATA_AUDIT.md) and Track A is a single snapshot with no repeated observations per customer over time.
- Track A's engineered recency features were checked for an obvious leakage pattern and did not show one, but this was not an exhaustive audit; if this project is extended, revisit `last_transaction` specifically given the counterintuitive result in STATISTICAL_ANALYSIS.md T4.
- Class weighting addresses imbalance in training but does not eliminate the precision/recall trade-off; both confusion matrices at the 0.50 threshold show meaningful numbers of both false positives and false negatives, which is normal for this kind of problem, not a defect specific to these models.
- Neither model has been reviewed for fairness or disparate impact across demographic groups, which would be a necessary step before any real-world use, prototype or otherwise.
