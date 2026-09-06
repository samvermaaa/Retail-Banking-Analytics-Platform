# Data Audit

This audit is based on direct inspection of the files uploaded for the project. No column, value, or statistic below was taken from memory of these datasets. Numbers were computed by loading each file with pandas.

## 1. Dataset Inventory

Two archives were uploaded: `archive.zip` and `bank_marketing.zip`. They contain three distinct data sources, none of which share a customer identifier (see section 4.4).

| File | Format | Rows | Columns | File size | Memory (loaded) | Source | Purpose |
|---|---|---|---|---|---|---|---|
| churn_prediction.csv | CSV | 28,382 | 21 | 3.66 MB | 8.54 MB | Bundled inside archive.zip with a README.md and a baseline notebook. No LICENSE file and no source URL in the notebook. | Customer-level balances, transaction activity, and churn flag |
| bank-full.csv | CSV (`;` delimited) | 45,211 | 17 | 4.50 MB | 25.75 MB | UCI Bank Marketing dataset (Moro et al., 2011), inside bank_marketing.zip > bank.zip | Full direct-marketing campaign log, Portuguese bank |
| bank.csv | CSV (`;` delimited) | 4,521 | 17 | 0.45 MB | 2.58 MB | 10% random sample of bank-full.csv, same archive | Small sample for fast iteration, not a distinct dataset |
| bank-additional-full.csv | CSV (`;` delimited) | 41,188 | 21 | 5.70 MB | 26.80 MB | UCI Bank Marketing dataset with social/economic context (Moro et al., 2014), inside bank_marketing.zip > bank-additional.zip | Campaign log enriched with five macroeconomic indicators |
| bank-additional.csv | CSV (`;` delimited) | 4,119 | 21 | 0.57 MB | 2.68 MB | 10% random sample of bank-additional-full.csv, same archive | Small sample for fast iteration, not a distinct dataset |

**License note on churn_prediction.csv:** the exact schema (customer_id, vintage, occupation categories, customer_nw_category, branch_code, and the rest) matches a Kaggle listing, "Bank Customer Churn Data" by Penta Krishna Kishore. The license field on that page (Apache 2.0) has been directly confirmed by viewing the live page, since this project's own tooling could not load it due to Kaggle's bot protection. The same schema also appears to originate from a data science course or bootcamp capstone assignment, based on identical problem-statement text found circulating independently of any Kaggle listing; this does not affect the license confirmation above, but is recorded as useful context. Full detail in `docs/DATA_SOURCES.md`.

**License on the UCI bank marketing files:** both bank.zip and bank-additional.zip include their own citation files (`bank-names.txt`, `bank-additional-names.txt`). The dataset is public for research use, citing Moro et al. (2011) and Moro et al. (2014) respectively. Source: UCI Machine Learning Repository, Bank Marketing dataset.

Only the two `-full` files are used going forward. `bank.csv` and `bank-additional.csv` are 10% random samples of the same population (confirmed: identical column sets) and add no new information, so they are kept in `raw/` for reference only.

## 2. Column Audit

### 2.1 churn_prediction.csv (28,382 rows, 21 columns)

| Column | Type | Missing % | Unique | Example / range | Analytical role |
|---|---|---|---|---|---|
| customer_id | int | 0% | 28,382 (unique) | 1 to 30,301 | Primary key |
| vintage | int | 0% | continuous | 73 to 2,476 (days; ~0.2 to 6.8 years) | Customer tenure |
| age | int | 0% | continuous | 1 to 90 | Demographic |
| gender | string | 1.85% | Male, Female | 16,548 Male / 11,309 Female / 525 missing | Demographic |
| dependents | float | 8.68% | mostly 0 to 9 | 0 to 52 (see finding 4.1) | Household indicator, needs cleaning |
| occupation | string | 0.28% | 5 categories | self_employed (61.6%), salaried (23.6%), student (7.3%), retired (7.1%), company (0.1%) | Segmentation input |
| city | float | 2.83% | 1,604 codes | 0 to 1,649 | City code, not a continuous value; high cardinality, needs grouping if used |
| customer_nw_category | int | 0% | 3 (1, 2, 3) | tier 2 (51.3%), tier 3 (35.6%), tier 1 (13.1%) | Bank-assigned net worth tier, undocumented meaning beyond the tier number |
| branch_code | int | 0% | 3,185 codes | 1 to 4,782 | High-cardinality identifier, not usable directly as a model feature |
| current_balance | float | 0% | continuous | -5,503.96 to 5,905,904.03 | Account balance |
| previous_month_end_balance | float | 0% | continuous | -3,149.57 to 5,740,438.63 | Account balance |
| average_monthly_balance_prevQ | float | 0% | continuous | 1,428.69 to 5,700,289.57 | Account balance |
| average_monthly_balance_prevQ2 | float | 0% | continuous | -16,506.10 to 5,010,170.10 | Account balance |
| current_month_credit | float | 0% | continuous | 0.01 to 12,269,845.39 | Transaction activity, heavy right skew |
| previous_month_credit | float | 0% | continuous | 0.01 to 2,361,808.29 | Transaction activity, heavy right skew |
| current_month_debit | float | 0% | continuous | 0.01 to 7,637,857.36 | Transaction activity, heavy right skew |
| previous_month_debit | float | 0% | continuous | 0.01 to 1,414,168.06 | Transaction activity, heavy right skew |
| current_month_balance | float | 0% | continuous | -3,374.18 to 5,778,184.77 | Account balance |
| previous_month_balance | float | 0% | continuous | -5,171.92 to 5,720,144.50 | Account balance |
| churn | int (0/1) | 0% | 2 | 0 = 81.5%, 1 = 18.5% | Target variable |
| last_transaction | string | 0% by null count, but see finding 4.2 | date-like strings + literal "NaT" | e.g. "2019-05-21" | Recency indicator, needs type conversion |

### 2.2 bank-full.csv (45,211 rows, 17 columns)

Column definitions below are drawn from `bank-names.txt`, included in the archive, not invented.

| Column | Type | "unknown" or missing marker | Range / categories | Analytical role |
|---|---|---|---|---|
| age | int | none | 18 to 95 | Demographic |
| job | string | 288 unknown (0.64%) | 12 categories (admin., blue-collar, management, technician, etc.) | Segmentation input |
| marital | string | none | married, single, divorced | Demographic |
| education | string | 1,857 unknown (4.11%) | unknown, primary, secondary, tertiary | Demographic |
| default | string (yes/no) | none coded unknown here | no (98.2%), yes (1.8%) | Credit risk flag |
| balance | int | none | -8,019 to 102,127 (average yearly balance, EUR) | Financial value |
| housing | string (yes/no) | none | has housing loan | Product ownership |
| loan | string (yes/no) | none | has personal loan | Product ownership |
| contact | string | 13,020 unknown (28.80%) | cellular, telephone, unknown | Channel |
| day | int | none | 1 to 31 (day of month only, no year) | Campaign timing |
| month | string | none | jan to dec | Campaign timing |
| duration | int | none | 0 to 4,918 seconds | Call length. Leakage risk, see DATA_LEAKAGE.md |
| campaign | int | none | 1 to 63 contacts this campaign | Engagement |
| pdays | int | none | -1 (never contacted, 81.7% of rows) to 871 | Days since last prior contact, needs a "never contacted" flag separate from the numeric value |
| previous | int | none | 0 to 275 | Contacts before this campaign |
| poutcome | string | 36,959 unknown (81.75%) | unknown, other, failure, success | Prior campaign outcome, mostly uninformative due to volume of unknowns |
| y | string (yes/no) | none | Target: subscribed term deposit. no = 88.3%, yes = 11.7% | Target variable |

### 2.3 bank-additional-full.csv (41,188 rows, 21 columns)

Column definitions drawn from `bank-additional-names.txt`, included in the archive.

| Column | Type | "unknown" marker | Range / categories | Analytical role |
|---|---|---|---|---|
| age | int | none | 17 to 98 | Demographic |
| job | string | 330 unknown (0.80%) | 12 categories | Segmentation input |
| marital | string | 80 unknown (0.19%) | divorced, married, single | Demographic |
| education | string | 1,731 unknown (4.20%) | 8 levels including basic.4y/6y/9y | Demographic |
| default | string | 8,597 unknown (20.87%) | no, yes, unknown | Credit risk flag, mostly unusable given unknown share |
| housing | string | 990 unknown (2.40%) | Product ownership |
| loan | string | 990 unknown (2.40%) | Product ownership |
| contact | string | none | cellular, telephone | Channel |
| month | string | none | jan to dec (no jan/feb present in the actual data based on campaign period) | Campaign timing |
| day_of_week | string | none | mon to fri | Campaign timing |
| duration | int | none | 0 to 4,918 seconds | Call length. Leakage risk, see DATA_LEAKAGE.md. The source documentation itself states this variable should be dropped for a realistic model. |
| campaign | int | none | 1 to 56 | Engagement |
| pdays | int | none | 0 to 999 (999 = never contacted, 96.3% of rows) | Same handling issue as bank-full.csv, more extreme here |
| previous | int | none | 0 to 7 | Contacts before this campaign |
| poutcome | string | none (uses "nonexistent" instead of "unknown") | failure, nonexistent, success | Prior campaign outcome |
| emp.var.rate | float | none | -3.4 to 1.4 | Macroeconomic, quarterly |
| cons.price.idx | float | none | 92.201 to 94.767 | Macroeconomic, monthly |
| cons.conf.idx | float | none | -50.8 to -26.9 | Macroeconomic, monthly |
| euribor3m | float | none | 0.634 to 5.045 | Macroeconomic, daily |
| nr.employed | float | none | 4,963.6 to 5,228.1 | Macroeconomic, quarterly |
| y | string | none | Target, same definition as bank-full. no = 88.7%, yes = 11.3% | Target variable |

Note: `bank-additional-full.csv` does not include a `balance` column. This is a real structural difference from `bank-full.csv`, not a loading error. The source documentation states the additional file omits some attributes present in the original for privacy reasons.

## 3. Data Quality Findings

### 3.1 churn_prediction.csv: impossible values in `dependents`
The column is mostly 0 to 9, but contains individual values of 52, 50, 36, and 25. A household cannot realistically have 52 dependents. These are very likely data entry errors (possibly a different field, like an ID, entered in the wrong column) and should be treated as invalid rather than capped-and-kept as if they were real.

### 3.2 churn_prediction.csv: `last_transaction` contains literal "NaT" strings
3,223 rows (11.4%) hold the literal text `"NaT"` instead of a date. This is a classic artifact of a datetime column being written to CSV with `NaT` as the null representation and then re-read as plain text, so pandas' missing-value counter reports 0% missing on this column when it is not actually 0%. These need to be converted to real null values before any recency calculation.

### 3.3 churn_prediction.csv: age outliers under 18
806 rows (2.8%) show an age under 18, including 4 rows with age = 1. Given that `occupation` includes a "student" category, some of these could be legitimate custodial or minor-held accounts rather than pure errors, but the youngest values (1 to 5 years old) are not plausible for an individual bank account holder. This needs an explicit decision in cleaning, not a silent drop.

### 3.4 churn_prediction.csv: negative balances
Several balance columns contain small numbers of negative values (9 to 23 rows out of 28,382 depending on the column). These are plausible if overdraft facilities exist, so they are not automatically treated as errors, but they are noted here for the cleaning step to decide on.

### 3.5 churn_prediction.csv: extreme right skew in credit and debit columns
Median `current_month_credit` is 0.61 while the maximum is 12,269,845.39. The 99.9th percentile is already 283,157, far below the maximum. This is a heavy-tailed distribution typical of transaction data (a small number of very large transfers), not necessarily corrupted data, but it will need log transformation or winsorization before it is used in clustering or regression, since raw values would dominate any distance-based method.

### 3.6 churn_prediction.csv: high-cardinality identifiers
`branch_code` has 3,185 unique values and `city` has 1,604, both stored as numeric codes rather than meaningful continuous measures. Neither should be fed into a model or clustering step as-is.

### 3.7 bank-full.csv and bank-additional-full.csv: "unknown" as a missing-value placeholder
Both files encode missing categorical values as the string "unknown" rather than a null. This does not show up in a standard `isna()` check and must be counted separately, which was done above. `poutcome` in bank-full.csv is unknown for 81.75% of rows, which limits how useful that column is on its own.

### 3.8 bank-full.csv and bank-additional-full.csv: `pdays` sentinel value
`pdays` uses -1 (bank-full) or 999 (bank-additional-full) to mean "never contacted before," mixed into what is otherwise a numeric day count. Left as-is, this sentinel would badly distort any mean, correlation, or regression involving `pdays`. It needs to be split into a binary "previously contacted" flag plus a numeric day count for the subset that was actually contacted before.

### 3.9 bank-additional-full.csv: 12 duplicate rows
12 rows are identical across all 21 columns, including macroeconomic values specified to three decimal places. Because the file has no customer identifier, it is not possible to confirm whether these are the same client contacted and logged twice, or a genuine coincidence. Given how unlikely an exact match across 21 fields is by chance, these are treated as likely duplicate log entries in the data quality summary, with a documented, reversible dedup step rather than a silent one.

### 3.10 bank-full.csv and bank-additional-full.csv: no year in the date fields
Both files record `day` (or `day_of_week`) and `month`, but never a year, even though the campaign spans May 2008 to November 2010 according to the source documentation. This means a true `dim_date` with real calendar dates cannot be reconstructed from the data as supplied. The date dimension will need to be built at the month/day-of-month grain only, with year treated as unknown.

### 3.11 Target imbalance
All three target-bearing datasets are imbalanced: churn at 18.5% positive, bank-full `y` at 11.7% positive, bank-additional-full `y` at 11.3% positive. Accuracy alone will be a misleading metric for any downstream model; this is flagged here so Agent 2 does not need to rediscover it.

## 4. Structural Findings That Affect Architecture

### 4.1 No shared customer identifier across the three data sources
`churn_prediction.csv` has its own `customer_id`. The two bank marketing files have no ID column at all, only anonymized per-contact rows. There is nothing in any of the three files that legitimately links a row in one dataset to a row in another. They also describe different institutions: the marketing files are explicitly a Portuguese bank's phone campaign log (Moro et al.), while the churn file's column set (vintage in days, occupation categories, net-worth tier, branch code) reflects a different bank and a different kind of record entirely, and nothing in the upload confirms the two are even the same country.

This means the three datasets cannot be joined into a single customer table. Building a single `dim_customer` that spans both source families would fabricate relationships that are not in the data. This project needs two separate fact groups: one for account balance, activity, and churn (from churn_prediction.csv), and one for marketing campaign response and product adoption (from bank-additional-full.csv, with bank-full.csv as a secondary reference where `balance` is needed). They can share a common metrics dictionary and a common `dim_date` grain, but not a common `dim_customer`.

### 4.2 Two marketing dataset variants are not supersets of each other
`bank-full.csv` has `balance` but no macroeconomic indicators. `bank-additional-full.csv` has five macroeconomic indicators but no `balance`. They are not the same rows with extra columns added; they come from different extraction passes over the same underlying campaign and have to be treated as related but distinct datasets, not merged.

**Decision:** `bank-additional-full.csv` is used as the primary marketing dataset going forward, because it has the richer feature set, includes the macroeconomic context that supports a more interesting analysis, and its own documentation is explicit about the duration leakage issue, which is directly useful for the statistical and modeling sections. `bank-full.csv` is retained as a secondary reference specifically where `balance` is needed for a bivariate question (for example, balance versus subscription), since that variable does not exist in the additional file.

## 5. Summary for Next Steps

- Two analytical tracks, not one merged customer base: balance and churn (churn_prediction.csv), and campaign response and product adoption (bank-additional-full.csv, with bank-full.csv as secondary).
- `duration` must be excluded from any realistic predictive model; documented separately in DATA_LEAKAGE.md.
- Cleaning must handle: literal "NaT" strings, impossible `dependents` values, the `pdays`/`poutcome` sentinel and unknown-as-missing pattern, and the 12 duplicate rows in bank-additional-full.csv.
- No true calendar date is reconstructable for the marketing data; the date dimension is month/day-of-month grain only.
- All three target variables are imbalanced and this must be stated wherever a model or classification metric is reported.
