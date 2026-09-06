# Metrics Dictionary

This is the single source of truth for metric definitions in this project. Agent 2 and Agent 3 should use these definitions rather than redefine them independently. Every metric below is backed by a column that exists in the cleaned data; none is aspirational.

## Track A: Balance, Behavior, and Churn

### Customer Count
- Definition: number of distinct customers.
- Formula: `COUNT(DISTINCT customer_id)`
- Source: `track_a.dim_customer`
- Granularity: any grouping of customer attributes (age group, occupation, segment).
- Filters: none by default.
- Business meaning: base size for any rate calculated on top of it.
- Known limitations: none.

### Average / Median Current Balance
- Definition: current account balance, mean and median.
- Formula: `AVG(current_balance)`, `MEDIAN(current_balance)`
- Source: `track_a.fact_customer_balance`
- Granularity: per customer, per segment, per demographic group.
- Filters: none by default.
- Business meaning: primary measure of account value.
- Known limitations: heavily right-skewed (DATA_AUDIT.md finding 3.5), so the mean can be pulled upward by a small number of very high-balance accounts. Report both the mean and the median, not the mean alone.

### Average Monthly Balance (Previous Quarter)
- Definition: average monthly balance over the previous quarter.
- Formula: `AVG(average_monthly_balance_prevQ)`
- Source: `track_a.fact_customer_balance`
- Granularity: per customer, per segment.
- Filters: none by default.
- Business meaning: a smoother balance measure than a single current snapshot.
- Known limitations: same right-skew caveat as current balance.

### Balance Growth
- Definition: change in balance from the previous month to the current month.
- Formula: `AVG(current_month_balance - previous_month_balance)`
- Source: `track_a.fact_customer_balance`
- Granularity: per customer, per segment.
- Filters: none by default.
- Business meaning: month-over-month trend in account value.
- Known limitations: `current_month_balance` and `current_balance` are related but not identical fields in the source data (DATA_DICTIONARY.md), and the exact difference is not documented. This metric intentionally uses the `_balance` fields specifically for a like-for-like month comparison; do not substitute `current_balance` into this formula.

### Churn Rate
- Definition: share of customers with churn = 1.
- Formula: `AVG(churn)`
- Source: `track_a.fact_customer_churn`
- Granularity: overall, and by any customer attribute or segment.
- Filters: none by default.
- Business meaning: headline retention metric for Track A.
- Known limitations: churn is 18.53% positive on the cleaned data (DATA_CLEANING.md); any model or comparison should account for this imbalance rather than rely on plain accuracy.

### Average Monthly Credit / Average Monthly Debit
- Definition: average total inflow (credit) and outflow (debit) in the current month.
- Formula: `AVG(current_month_credit)`, `AVG(current_month_debit)`
- Source: `track_a.fact_customer_activity`
- Granularity: per customer, per segment.
- Filters: none by default.
- Business meaning: transactional engagement.
- Known limitations: extremely heavy right skew (DATA_AUDIT.md finding 3.5); a small number of very large transactions can dominate the mean. Consider median or a transformed value for skew-sensitive comparisons.

### Transaction Recency
- Definition: days between a customer's last transaction and the latest observed transaction date in the data (2019-12-31).
- Formula: `date_diff('day', last_transaction, DATE '2019-12-31')`
- Source: `track_a.fact_customer_activity`, computed in `track_a.track_a_customer_profile`
- Granularity: per customer, per segment, or banded (see the recency bands in STATISTICAL_ANALYSIS.md, T4).
- Filters: excludes the 3,223 customers (11.4%) whose `last_transaction` could not be parsed.
- Business meaning: how recently a customer has actively used the account.
- Known limitations: customers with an unparseable `last_transaction` are excluded from this metric rather than assumed to be inactive. STATISTICAL_ANALYSIS.md T4 found this group actually has the lowest churn rate observed in Track A, which argues directly against treating a missing date as a proxy for disengagement.

## Track B: Campaign Response and Product Adoption

### Campaign Observation Count
- Definition: number of campaign contact records. Not a customer count; there is no persistent customer identity in this data (DATA_AUDIT.md section 4.1).
- Formula: `COUNT(*)`
- Source: `track_b.marketing_observation` (primary, 41,176 rows) or `track_b.marketing_observation_bank_full` (secondary, 45,211 rows)
- Granularity: any grouping of contact attributes.
- Filters: none by default.
- Business meaning: base size for any Track B rate.
- Known limitations: the two source tables are not the same population and must never be summed together.

### Product Adoption Rate
- Definition: share of contacts where the client subscribed to a term deposit.
- Formula: `AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END)`
- Source: `track_b.marketing_observation`
- Granularity: overall (11.27% on the primary dataset), or sliced by job, education, age band, housing/loan status, or previous contact history (see `track_b.track_b_adoption_summary` and STATISTICAL_ANALYSIS.md).
- Filters: none by default.
- Business meaning: headline conversion metric for Track B.
- Known limitations: 11.27% positive on the primary dataset (11.70% on bank-full.csv); treat as an imbalanced target, same caveat as Track A's churn rate.

### Previous Campaign Contact Rate
- Definition: share of contacts where the client had been reached in a prior campaign.
- Formula: `AVG(previous_contact_flag)`
- Source: `track_b.marketing_observation` (3.68%) or `track_b.marketing_observation_bank_full` (18.26%)
- Granularity: overall, or by segment.
- Filters: none by default.
- Business meaning: measures how much of the contact base is a repeat audience versus a cold one.
- Known limitations: the two source tables give materially different rates (3.68% versus 18.26%), a real feature of the two extracts, not a computation error (documented in DATA_CLEANING.md).

### Adoption Rate by Previous Outcome
- Definition: product adoption rate, split by the result of a prior campaign contact (success, failure, or no prior contact).
- Formula: `AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0 END)` grouped by `poutcome`
- Source: `track_b.marketing_observation`
- Granularity: by `poutcome` category.
- Filters: none by default.
- Business meaning: the strongest predictor of adoption found in this project (STATISTICAL_ANALYSIS.md T5, T6).
- Known limitations: closely correlated with Previous Campaign Contact Rate by construction; do not treat as two independent signals.

Adoption Rate by Job, Education, Age Band, and Housing/Loan Status are the same Product Adoption Rate formula above, grouped by the named attribute. They are not separately defined metrics; they are documented once here to avoid four near-duplicate entries. Results for each are in `track_b.track_b_adoption_summary` and STATISTICAL_ANALYSIS.md (T7, T8).
