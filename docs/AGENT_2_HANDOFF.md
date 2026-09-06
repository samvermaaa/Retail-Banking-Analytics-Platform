# Agent 2 Handoff

This covers both tracks. Read DATA_LEAKAGE.md and STATISTICAL_ANALYSIS.md before building anything; the leakage exclusion for Track B is enforced in code, not just described here.

## Data available

### Track A
- Cleaned file: `data/processed/churn_clean.csv` (28,382 rows, one row per customer)
- Segment assignments: `data/processed/segment_assignments.csv` (`customer_id`, `segment`, k = 4)
- Database: `db/banking_analytics.duckdb`, schema `track_a` (`dim_customer`, `fact_customer_balance`, `fact_customer_activity`, `fact_customer_churn`), plus the view `track_a.track_a_customer_profile` which already joins all four tables on `customer_id`.

### Track B
- Primary cleaned file: `data/processed/bank_additional_clean.csv` (41,176 rows, one row per campaign contact, 12 exact duplicates already removed)
- Secondary cleaned file: `data/processed/bank_full_clean.csv` (45,211 rows), used only where `balance` is needed since the primary file does not include it
- Database: `db/banking_analytics.duckdb`, schema `track_b` (`marketing_observation`, `marketing_observation_bank_full`)
- Feature configuration: `src/data/feature_config.py` defines `MODEL_READY_FEATURES`, which already excludes `duration`. Import this list rather than reading columns off the CSV directly.

Track A and Track B are never joined at the row level. They describe different populations (DATA_AUDIT.md section 4.1).

## Recommended modeling targets

- Track A: `churn` (binary, 18.53% positive on the cleaned data)
- Track B: `y` (binary, 11.27% positive on `bank_additional_clean.csv`, 11.70% on `bank_full_clean.csv`)

## Features available

### Track A
All columns in `churn_clean.csv` except `customer_id` (identifier) and `churn` (target) are candidate features: `vintage`, `age`, `age_under_18_flag`, `gender`, `dependents`, `occupation`, `city`, `customer_nw_category`, `branch_code`, and the balance/credit/debit columns. `city` and `branch_code` are high-cardinality codes (1,604 and 3,185 unique values) and are not usable as raw categorical features without grouping or a different encoding strategy. `segment` (from `segment_assignments.csv`) is also available as a feature or as a way to stratify evaluation, but it was built from a subset of these same underlying columns (see SEGMENTATION_DECISION.md), so using both the raw features and the segment together in one model is partially redundant.

### Track B
Use `MODEL_READY_FEATURES` from `src/data/feature_config.py`: `age`, `job`, `marital`, `education`, `default`, `housing`, `loan`, `contact`, `month`, `day_of_week`, `campaign`, `previous_contact_flag`, `days_since_previous_contact`, `previous`, `poutcome`, and the five macroeconomic indicators (`emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed`). `duration` is present in the cleaned CSV for descriptive use only and is excluded from this list by construction.

`previous_contact_flag`/`days_since_previous_contact` and `poutcome` are closely related (STATISTICAL_ANALYSIS.md T5, T6, Cramér's V 0.325 and 0.321). Check for multicollinearity before using all of them together in a linear model.

## Target definitions

- Track A `churn`: 1 = churned, 0 = retained. No transformation applied.
- Track B `y`: stored as text ("yes"/"no") in the cleaned CSVs. Note that DuckDB's CSV auto-detection will silently infer this column as BOOLEAN and convert "yes"/"no" to true/false if loaded with `read_csv_auto` without an explicit type override; `sql/03_load_transformations.sql` handles this correctly with `read_csv(..., types={'y': 'VARCHAR'})`, but if you load the CSV independently, watch for this.

## Leakage concerns

- `duration` (Track B): known only after a call happens or ends. Excluded from `MODEL_READY_FEATURES`. Full reasoning in DATA_LEAKAGE.md. It may be used in a clearly labeled benchmark comparison showing the effect of including it, never in a model meant to guide who to call.
- No leakage variable was identified in Track A during this phase. `last_transaction` / transaction recency should get a second look once a model is being built, given the counterintuitive result in STATISTICAL_ANALYSIS.md T4 (customers with no parseable transaction date have the lowest churn rate of any group, not the highest).

## Missing-value decisions

- Track A `dependents`: 2,468 rows (8.7%) missing, including 5 rows where an implausible raw value (25 to 52) was converted to missing during cleaning. Not imputed.
- Track A `last_transaction`: 3,223 rows (11.4%) missing, converted from a literal "NaT" string during cleaning. Not imputed.
- Track A `age_under_18_flag`: 806 rows (2.8%) flagged, not removed. Decide explicitly whether to include or exclude them from any age-based model.
- Track B: "unknown" is retained as an explicit category in `job`, `marital`, `education`, `default`, `housing`, `loan`, not imputed. See DATA_CLEANING.md for the per-column rates (`default` is 20.88% unknown in bank_additional_clean.csv, the largest of these).

## Categorical encoding considerations

- Track B `job`, `education`, `poutcome`, `month`, `day_of_week`/`contact` are nominal categoricals with no natural order; one-hot or target encoding are both reasonable, but if using target encoding, fit it only on a training split to avoid leaking the target into the encoding itself.
- Track A `customer_nw_category` (1, 2, 3) may be ordinal; SEGMENTATION_DECISION.md found a directional pattern suggesting tier 1 may be the bank's highest net worth tier, but this is inferred from the data, not confirmed by documentation. Treat the ordering as a hypothesis to check, not a given.

## Class imbalance

Both targets are imbalanced: Track A churn at 18.53% positive, Track B adoption at 11.27% (primary) or 11.70% (secondary) positive. Plain accuracy will be misleading for either. Use precision/recall, ROC-AUC/PR-AUC, or a cost-weighted approach appropriate to the actual business use case.

## Segmentation results

Track A only, k = 4, silhouette 0.1983 (weak-to-moderate structure, documented honestly in SEGMENTATION_DECISION.md, not overstated). Segment sizes: 5,429 / 11,813 / 7,101 / 4,039. Segment 2 ("High Activity, High Churn") has the highest churn rate of any segment at 25.0%, against 15.0% to 18.0% elsewhere, and is the most actionable finding from the segmentation for a churn model to explain or target.

## Statistical findings

Full detail in STATISTICAL_ANALYSIS.md. Highlights:
- Track A: current balance is the strongest signal found for churn (rank-biserial 0.42). Age group and net worth tier are weak (Cramér's V 0.046 and 0.017).
- Track B: prior campaign contact and prior campaign outcome are by far the strongest signals for adoption (Cramér's V 0.325 and 0.321), followed by age band (0.172, non-linear/U-shaped) and job (0.153).

## SQL views available

`track_a.track_a_customer_profile`, `track_a.track_a_churn_summary`, `track_b.track_b_campaign_summary`, `track_b.track_b_adoption_summary`, all in `db/banking_analytics.duckdb`.
