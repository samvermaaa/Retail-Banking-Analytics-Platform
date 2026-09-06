# Segmentation Decision

Scope: Track A (churn_prediction customers) only. Track B has no persistent customer identity (see DATA_AUDIT.md section 4.1), so a customer segmentation is not methodologically meaningful there. `src/data/segment.py` produces this output and is the source of every number below.

## Feature selection

Features used: `vintage`, `age`, `current_balance`, `average_monthly_balance_prevQ`, `current_month_credit`, `current_month_debit`.

`churn` is excluded deliberately. Including the target in an unsupervised segmentation would let the clusters partly encode the outcome they are later used to explain, which is a form of target leakage even outside a supervised model. `customer_nw_category` and `occupation` are excluded as clustering inputs for a different reason: `customer_nw_category` is already a bank-assigned tier, and using it as an input risks the clustering just reproducing that existing label rather than finding anything new. Both are used afterward to profile and sanity-check the resulting segments, not to build them. `dependents` is excluded because of its missing-value rate and the invalid values already documented in DATA_CLEANING.md; adding it would have required an imputation decision that the other six features do not need. `city` and `branch_code` are excluded as documented in DATA_AUDIT.md: they are identifiers, not continuous measures.

The four monetary columns (`current_balance`, `average_monthly_balance_prevQ`, `current_month_credit`, `current_month_debit`) are heavily right-skewed with extreme outliers, documented in DATA_AUDIT.md finding 3.5. Each was transformed with `arcsinh` before scaling. Unlike a log transform, `arcsinh` is defined for negative values, which matters here since `current_balance` can be negative. All six features were then standardized (zero mean, unit variance) before clustering. `vintage` and `age` were standardized without the arcsinh transform, since neither is heavily skewed.

## Choosing k

K-means was evaluated for k = 2 through 6, random_state = 42, n_init = 10.

| k | Silhouette | Davies-Bouldin | Cluster sizes |
|---|---:|---:|---|
| 2 | 0.2108 | 1.9212 | 11,032 / 17,350 |
| 3 | 0.1912 | 1.6923 | 6,169 / 9,756 / 12,457 |
| 4 | 0.1983 | 1.5528 | 5,429 / 11,813 / 7,101 / 4,039 |
| 5 | 0.1848 | 1.4801 | 5,674 / 4,501 / 6,500 / 8,396 / 3,311 |
| 6 | 0.1957 | 1.4443 | 3,948 / 6,303 / 4,868 / 6,225 / 4,285 / 2,753 |

No value of k produces a strong silhouette score. All five are in the 0.18 to 0.21 range, which by conventional interpretation (above roughly 0.5 is strong structure, below roughly 0.25 is weak) indicates overlapping clusters rather than cleanly separated ones. This is stated plainly rather than glossed over: the underlying feature space does not have sharply distinct customer groups. What follows is a defensible descriptive segmentation for business communication, not evidence of naturally occurring, well-separated customer types.

k = 2 has the single highest silhouette score, but produces only a coarse two-way split. Davies-Bouldin keeps improving as k increases, which is a common pattern and not on its own a reason to pick the largest k tested. **k = 4 was selected**: its silhouette (0.1983) is close to the maximum observed and clearly above k = 3 and k = 5, its Davies-Bouldin index is meaningfully better than k = 2 or k = 3, none of its four clusters is a tiny leftover group (the smallest is 4,039 customers, 14.2% of the base), and it gives Agent 2 and Agent 3 more than a binary split to work with while still being interpretable. k = 6 has a similar silhouette to k = 4 with a marginally better Davies-Bouldin, but splits the base into six smaller, harder-to-name groups without a clear interpretability gain over four. k was not chosen because four is a conventional or attractive number; the reasoning above is what would change if the metrics had come out differently.

## Cluster profiles

| Segment | Customers | % of base | Avg age | Avg tenure (days) | Avg balance | Median balance | Avg monthly credit | Avg monthly debit | Churn rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 5,429 | 19.1% | 54.9 | 2,142 | 24,072.95 | 12,608.74 | 5,918.74 | 6,577.96 | 15.0% |
| 1 | 11,813 | 41.6% | 46.1 | 2,200 | 2,950.34 | 2,509.02 | 48.30 | 438.79 | 17.0% |
| 2 | 7,101 | 25.0% | 47.1 | 2,143 | 3,862.69 | 2,705.49 | 8,843.52 | 8,248.88 | 25.0% |
| 3 | 4,039 | 14.2% | 47.4 | 1,614 | 4,085.50 | 3,020.82 | 480.62 | 1,082.45 | 18.0% |

Occupation mix is broadly similar across all four segments (self-employed is 61 to 64% of every segment), so occupation does not distinguish these groups. `customer_nw_category` shows a directional pattern worth noting: segment 0 (the highest-balance group) has a higher share of tier 1 customers (22.3%, versus 13.1% overall) and a lower share of tier 3 (22.6%, versus 35.6% overall) than the base population. The source data does not document what tiers 1, 2, and 3 represent, but this pattern is consistent with tier 1 being the bank's highest net worth tier. This is stated as an observation from the data, not a confirmed fact about the tier definitions.

## Labels

Labels are descriptive summaries of the profile table above, not claims about customer intent.

- **Segment 0, "High Balance, Low Activity" (19.1%).** By far the highest average and median balance of any segment, oldest average age, longest tenure, and the lowest churn rate (15.0%). Transaction activity is present but moderate relative to balance size.
- **Segment 1, "Mass Retail" (41.6%).** The largest segment. Lowest balance and by a wide margin the lowest transaction activity (average monthly credit of 48.30 against 5,918.74 to 8,843.52 in the other segments). Churn rate close to the overall average.
- **Segment 2, "High Activity, High Churn" (25.0%).** The highest transaction activity of any segment on both credit and debit, moderate balance, and the highest churn rate by a clear margin (25.0% versus 15 to 18% elsewhere). This is the most actionable segment for retention work: high engagement did not translate into lower churn here, which runs against a simple "more active customers are more loyal" assumption.
- **Segment 3, "Newer Customers" (14.2%).** Meaningfully shorter tenure than every other segment (1,614 days versus 2,142 to 2,200), moderate balance, and low-to-moderate activity. This reads as a still-developing relationship rather than a settled one.

## Files produced

- `data/processed/segment_assignments.csv`: `customer_id`, `segment` for all 28,382 customers.
- `data/processed/segment_profiles.csv`: the profile table above.
- `src/data/segment.py`: the full, reproducible pipeline, including the k = 2 to 6 evaluation.
