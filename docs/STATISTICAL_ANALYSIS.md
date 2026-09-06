# Statistical Analysis

All tests below run against the cleaned datasets (`data/processed/`), computed through the SQL views in `sql/04_track_a_analytics.sql` and `sql/05_track_b_analytics.sql`, with the tests themselves run in scipy. Every number here came from an executed test, not an assumption.

Test selection follows the shape of the data rather than a default choice. The balance and credit/debit columns are heavily right-skewed (documented in DATA_AUDIT.md), so comparisons involving them use the Mann-Whitney U test rather than a t-test, which assumes roughly normal, equal-variance groups that this data does not have. Categorical-by-categorical comparisons use chi-square with Cramér's V as the effect size. None of this should be read as a causal claim: all data here is observational.

## Track A: Balance, Behavior, and Churn

### T1. Current balance, churned vs retained customers

- H0: current balance has the same distribution for churned and retained customers.
- H1: the distributions differ.
- Test: Mann-Whitney U (balance is heavily right-skewed, so medians and ranks are compared rather than means).
- n(churned) = 5,260, n(retained) = 23,122
- U = 35,267,327.5, p < 0.001
- Effect size: rank-biserial correlation = 0.42 (large by conventional thresholds)
- Median balance: churned 1,540.88, retained 3,643.12. Bootstrap 95% CI for the median difference: -2,204.24 to -2,004.09.
- Interpretation: churned customers have meaningfully lower current balances than retained customers. This is the largest effect size found in Track A and lines up with the balance-quartile pattern below. It is an association, not evidence that low balance causes churn; the reverse (customers who intend to leave draw down their balance first) is at least as plausible from this data alone.

### T2. Churn rate by age group

- H0: churn rate is independent of age group.
- Test: chi-square test of independence, 7 age groups x churn.
- n = 28,382, chi-square = 59.35, df = 6, p < 0.001
- Effect size: Cramér's V = 0.046 (small)
- Interpretation: the association is statistically significant given the sample size, but the effect is small. Churn ranges from 12.9% (under 18) to 20.5% (26-35), a real but modest spread. Age group alone is a weak segmentation variable for churn.

### T3. Churn rate by customer net worth category

- H0: churn rate is independent of net worth tier.
- Test: chi-square test of independence, 3 tiers x churn.
- n = 28,382, chi-square = 7.96, df = 2, p = 0.019
- Effect size: Cramér's V = 0.017 (negligible)
- Interpretation: statistically significant at the 0.05 level only because of the large sample size. Churn rates across tiers (19.1%, 17.9%, 19.2%) are close enough that this variable has no practical value for identifying churn risk on its own.

### T4. Churn rate by transaction recency

- H0: churn rate is independent of days since last transaction.
- Test: chi-square test of independence, 5 recency bands x churn.
- n = 28,382, chi-square = 327.08, df = 4, p < 0.001
- Effect size: Cramér's V = 0.107 (small to moderate, the largest categorical effect in Track A)
- Interpretation: churn is highest in the 31-90 day band (22.7%) and lowest among customers with no parseable last_transaction date (9.3%). The second result is counterintuitive: a missing transaction date is not, in this data, a sign of a disengaged customer. This needs caution rather than a clean recency story. It is possible the missing dates reflect a different data collection process for a subset of accounts rather than an absence of activity, and this should be investigated further before being used as a churn signal.

## Track B: Campaign Response and Product Adoption

### T5. Adoption rate, previously contacted vs never contacted

- H0: adoption rate is the same for clients previously contacted and clients never contacted before this campaign.
- Test: chi-square test of independence (2x2), plus a normal-approximation two-proportion comparison for a direct effect estimate.
- n = 41,176, chi-square = 4,341.34, df = 1, p < 0.001
- Effect size: Cramér's V = 0.325 (large for this kind of categorical comparison)
- Adoption rate: previously contacted 63.8%, never contacted 9.3%. Difference in proportions: 54.6 percentage points, 95% CI 52.1 to 57.0 points.
- Interpretation: this is the strongest relationship found anywhere in this analysis. A client who responded to a prior campaign contact is far more likely to subscribe now. This is the clearest, most actionable signal in Track B for prioritizing outreach.

### T6. Adoption rate by previous campaign outcome

- H0: adoption rate is independent of the prior campaign's outcome.
- Test: chi-square test of independence, 3 categories x adoption.
- n = 41,176, chi-square = 4,230.14, df = 2, p < 0.001
- Effect size: Cramér's V = 0.321 (large)
- Interpretation: adoption is 65.1% following a prior success, 14.2% following a prior failure, and 8.8% where no prior campaign exists. This overlaps substantially with T5, since prior contact and prior outcome are closely related by construction; they should not be treated as two independent signals in a model.

### T7. Adoption rate by job

- H0: adoption rate is independent of job category.
- Test: chi-square test of independence, 12 categories x adoption.
- n = 41,176, chi-square = 961.74, df = 11, p < 0.001
- Effect size: Cramér's V = 0.153 (small to moderate)
- Interpretation: students (31.4%) and retired clients (25.3%) adopt at more than double the overall rate (11.3%), while blue-collar workers (6.9%) and services workers (8.1%) adopt at below-average rates. Occupation is a genuinely useful segmentation variable here, unlike net worth tier in Track A.

### T8. Adoption rate by age band

- H0: adoption rate is independent of age band.
- Test: chi-square test of independence, 6 age bands x adoption.
- n = 41,176, chi-square = 1,214.05, df = 5, p < 0.001
- Effect size: Cramér's V = 0.172 (moderate, the largest demographic effect in Track B)
- Interpretation: the relationship is not linear. Adoption is 47.3% for clients 65 and older and 24.0% for clients under 25, against 8.6% to 13.6% for every band in between. A simple young-versus-old or linear-age comparison would have missed this. A follow-up rank-based comparison of raw age between adopters and non-adopters (Mann-Whitney U, rank-biserial = 0.022, p = 0.016, median age 37 vs 38) shows only a trivial difference, which confirms the relationship is specifically about the two tails of the age distribution, not a general age trend. Report age as a banded categorical feature, not a raw linear term, if used in a model.

### T9. Balance, adopters vs non-adopters (bank-full.csv, secondary dataset)

- H0: balance has the same distribution for adopters and non-adopters.
- Test: Mann-Whitney U (balance is heavily right-skewed here as well).
- n(adopted) = 5,289, n(not adopted) = 39,922
- U = 124,589,983.5, p < 0.001
- Effect size: rank-biserial correlation = -0.18 (small)
- Median balance: adopters 733.00, non-adopters 417.00. Bootstrap 95% CI for the median difference: 273.00 to 376.00.
- Interpretation: adopters carry a higher balance, but the effect is smaller than the previous-contact or age-band effects above. Balance is a secondary signal here, not a primary one, and this test is only possible using bank-full.csv, since bank-additional-full.csv does not include balance.

## Summary table

| Analysis | Test | Effect Size | 95% CI | p-value | Interpretation |
|---|---|---:|---:|---:|---|
| T1 balance vs churn | Mann-Whitney U | rank-biserial 0.42 | median diff -2204 to -2004 | <0.001 | Large: churned customers hold less balance |
| T2 churn vs age group | Chi-square | Cramér's V 0.046 | not computed for V | <0.001 | Small: weak segmentation value |
| T3 churn vs nw category | Chi-square | Cramér's V 0.017 | not computed for V | 0.019 | Negligible: no practical value |
| T4 churn vs recency | Chi-square | Cramér's V 0.107 | not computed for V | <0.001 | Small-moderate: counterintuitive "no date" result needs follow-up |
| T5 adoption vs prior contact | Chi-square | Cramér's V 0.325 | prop diff 52.1 to 57.0 pts | <0.001 | Large: strongest relationship in the project |
| T6 adoption vs prior outcome | Chi-square | Cramér's V 0.321 | not computed for V | <0.001 | Large, overlaps with T5 |
| T7 adoption vs job | Chi-square | Cramér's V 0.153 | not computed for V | <0.001 | Small-moderate: useful segmentation variable |
| T8 adoption vs age band | Chi-square | Cramér's V 0.172 | not computed for V | <0.001 | Moderate, non-linear (U-shaped) |
| T9 balance vs adoption | Mann-Whitney U | rank-biserial -0.18 | median diff 273 to 376 | <0.001 | Small: secondary signal |

A confidence interval is reported wherever it could be computed directly (proportion differences, bootstrap median differences). Cramér's V does not have a standard analytic confidence interval and none is fabricated here; where a CI on V is needed, it should be computed by bootstrap in a later phase rather than assumed.

## Caveats that apply to every test above

- All p-values are small partly because sample sizes are large (28,382 and 41,176 rows). Statistical significance is reported alongside effect size specifically so a small, practically unimportant effect (T3) is not confused with a large, practically important one (T5).
- Every relationship here is observational. None of this analysis establishes that any variable causes churn or causes adoption.
- T5 and T6 measure closely related things (prior contact and prior outcome). Using both in a downstream model would be redundant, not two independent pieces of evidence.
