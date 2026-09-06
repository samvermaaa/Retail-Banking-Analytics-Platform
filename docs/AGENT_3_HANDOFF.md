# Agent 3 Handoff

## Validated KPIs

All defined precisely in METRICS_DICTIONARY.md; summarized here with their current values.

### Track A
- Customer count: 28,382
- Churn rate: 18.53%
- Average current balance: right-skewed, report median (2,509 to 12,609 depending on segment) alongside the mean, not the mean alone
- Balance growth: `current_month_balance - previous_month_balance`, average
- Transaction recency: excludes 3,223 customers (11.4%) with an unparseable last transaction date

### Track B
- Campaign observation count: 41,176 (primary) or 45,211 (secondary); these are not additive, they are different extracts of the same underlying campaign
- Product adoption rate: 11.27% (primary), 11.70% (secondary)
- Previous campaign contact rate: 3.68% (primary), 18.26% (secondary), genuinely different between the two extracts

## Recommended dashboard pages

1. **Executive overview.** Customer count and churn rate (Track A), campaign observation count and adoption rate (Track B), shown side by side as two separate headline sections. Do not present them as one combined "customer" metric; they are different populations.
2. **Track A: Customer Segmentation.** The four segments from SEGMENTATION_DECISION.md, sized and colored by customer count, with balance, activity, and churn rate as the profiling metrics per segment. Segment 2 ("High Activity, High Churn") should be visually flagged given its 25.0% churn rate against 15 to 18% elsewhere.
3. **Track A: Balance and Churn.** Churn rate by balance quartile (a strong pattern: 40.1% in the lowest quartile versus roughly 10 to 12% in the top three), by age group, and by recency band, sourced from `track_a.track_a_churn_summary`.
4. **Track B: Campaign and Product Adoption.** Adoption rate by job, education, age band, and previous contact history, sourced from `track_b.track_b_adoption_summary`. Prior contact history is the single strongest lever here (63.8% adoption if previously contacted versus 9.3% if not) and should be the most prominent chart on this page.
5. **Track B: Balance Context (secondary).** Adoption rate by balance quartile, using `bank_full_clean.csv` only, clearly labeled as a secondary dataset that is not part of the same extract as the rest of the campaign analysis.

## Required visualizations

| Chart | Data source | Notes |
|---|---|---|
| Churn rate by balance quartile | `track_a.track_a_churn_summary` (or the Q4 query in `sql/04_track_a_analytics.sql`) | Bar chart, four bars |
| Segment profile comparison | `data/processed/segment_profiles.csv` | Small multiples or a grouped bar chart across the four segments |
| Adoption rate by previous contact | `track_b.marketing_observation` (Q7 in `sql/05_track_b_analytics.sql`) | Two-bar comparison, largest effect in the project |
| Adoption rate by job | `track_b.track_b_adoption_summary` | Sorted bar chart, 12 categories |
| Adoption rate by age band | `sql/05_track_b_analytics.sql` Q2 | Note the U-shape (young and old adopt more, middle ages less); do not use a simple line chart that implies a linear trend |
| Churn rate by recency band | `sql/04_track_a_analytics.sql` Q5 | Include the "no valid date" category explicitly rather than dropping it; it is the lowest-churn group, which is a genuine and slightly counterintuitive finding |

## Filters

Recommended filter fields: Track A: `customer_nw_category`, `occupation`, `segment`, age band. Track B: `job`, `education`, `month`, `previous_contact_flag`. Do not build a filter that applies across both tracks at once (for example, a single "customer segment" filter touching both), since there is no shared customer entity to filter on.

## Business insights to surface

- Track A: current balance is the strongest signal associated with churn found in this project (rank-biserial 0.42); the lowest balance quartile churns at 40.1% against roughly 10 to 12% for the top three quartiles.
- Track A: the "High Activity, High Churn" segment (25.0% of customers, 25.0% churn rate) is the most actionable segment. High transaction activity did not correspond to lower churn in this segment.
- Track B: previous campaign contact is the strongest signal for adoption (63.8% versus 9.3%). Prioritizing repeat outreach to previously-responsive clients is the clearest, most directly supported recommendation from this analysis.
- Track B: adoption by age is U-shaped, not linear. Clients under 25 and 65+ adopt at roughly double to four times the rate of clients 35 to 54.

These are the only findings that should be surfaced as headline insights. Anything not listed here and not directly traceable to STATISTICAL_ANALYSIS.md or the SQL business questions should not be presented as a finding.

## Data limitations

- Track A and Track B cannot be shown as a single unified customer view. Any dashboard page that implies a shared customer base across both tracks would misrepresent the data.
- Both target variables are imbalanced (18.53% and 11.27%/11.70% positive). Any KPI or model output shown on the dashboard should be labeled clearly enough that a viewer does not read a high accuracy figure as more impressive than it is.
- Track B's `bank_full_clean.csv` and `bank_additional_clean.csv` are not the same population and should never be combined into one total.

## Date limitations

Neither Track B source file contains a year, only day/month or day-of-week/month. No calendar-date axis is possible for Track B; any month-based chart should be labeled as relative/seasonal rather than tied to 2008 to 2010 specifically. Track A's `last_transaction` is a genuine calendar date (range 2018-12-31 to 2019-12-31) and does not have this limitation.

## Phase 3 addendum: models built

Full detail in MODELING.md. This section adds what the dashboard needs from the modeling layer; everything above from Phase 2 still stands.

### Models and final metrics

Random Forest was selected for both tracks (highest PR-AUC and ROC-AUC, consistent with cross-validation). Logistic Regression and Decision Tree were also trained for comparison and are documented in MODELING.md, not just the winner.

| Track | Model | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|
| A (churn) | Random Forest | 0.8422 | 0.6214 | 0.5707 | 0.6141 | 0.5916 |
| B (adoption) | Random Forest | 0.8128 | 0.4766 | 0.4194 | 0.6304 | 0.5037 |

Precision/recall above are at the default 0.50 threshold. A full threshold sweep (0.10 to 0.90) is in `data/model_outputs/track_a_threshold_analysis.csv` and `track_b_threshold_analysis.csv`; if the dashboard shows a "predicted risk" or "predicted adoption" KPI, do not hardcode 0.50 as if it were the recommended operating point, since MODELING.md section 13 found lower thresholds trade a small amount of precision for a meaningfully higher recall on both tracks.

### Important features

Track A: `current_balance` dominates (permutation importance 0.310, far ahead of the next feature), followed by `average_monthly_balance_prevQ` and `current_month_debit`. This lines up with the Phase 2 statistical finding that balance is the strongest signal for churn.

Track B: the five macroeconomic indicators dominate, led by `euribor3m` and `nr.employed`, ahead of any individual client attribute including `previous_contact_flag`. If the dashboard has a feature-importance chart for Track B, the macroeconomic variables should be shown, not just demographic ones, or the chart will misrepresent what the model actually relies on.

### Useful model outputs for the dashboard

- `data/model_outputs/track_a_permutation_importance.csv` and `track_b_permutation_importance.csv`: ranked feature importance, ready to chart directly.
- `data/model_outputs/track_a_threshold_analysis.csv` and `track_b_threshold_analysis.csv`: precision/recall/F1 at every threshold from 0.10 to 0.90, useful for an interactive threshold slider if the dashboard tooling supports one.
- `data/model_outputs/track_a_model_comparison.csv` and `track_b_model_comparison.csv`: the three-model comparison table, useful for a methodology page.

### Business questions the dashboard should be able to answer

- Which customers have elevated predicted churn risk, and does that align with the Phase 2 segments (particularly Segment 2, "High Activity, High Churn")?
- How does the precision/recall trade-off change if outreach capacity changes, using the threshold sweep data?
- Which macroeconomic conditions historically coincided with higher predicted adoption in Track B?

### Limitations that must be shown in the dashboard

- These are prototype models, not validated or deployed systems. Any dashboard page showing model output should say so.
- Neither model has been checked for fairness or disparate impact across demographic groups. Do not present model output as a vetted risk score without that caveat visible.
- Track A and Track B models are independent; a customer-level score from one has no counterpart in the other, since the two tracks do not share a customer identity.
- Feature importance and coefficients describe association, not causation. Avoid dashboard language like "balance causes retention"; use "associated with" or "predictive of" instead, consistent with MODELING.md.
