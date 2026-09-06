# Data Cleaning

Cleaning is implemented in `src/data/clean.py` and validated in `src/data/validate.py`, both run against the raw files in `raw/`. Neither script modifies the raw files. Cleaned outputs are written to `data/processed/`.

## Summary

| Dataset | Original Rows | Removed Rows | Final Rows | Main Transformations |
|---|---:|---:|---:|---|
| churn_clean.csv | 28,382 | 0 | 28,382 | Literal "NaT" strings converted to real missing values in `last_transaction`; 5 implausible `dependents` values (25, 32, 36, 50, 52) set to missing; `age_under_18_flag` added, no rows removed |
| bank_additional_clean.csv | 41,188 | 12 | 41,176 | Exact duplicate rows removed; `pdays` sentinel (999) converted to `previous_contact_flag` and `days_since_previous_contact`; "unknown" categorical values retained as their own category |
| bank_full_clean.csv | 45,211 | 0 | 45,211 | `pdays` sentinel (-1) converted to `previous_contact_flag` and `days_since_previous_contact`; "unknown" categorical values retained as their own category; no duplicate rows found |

No rows were removed from either the churn dataset or bank-full.csv. The only row removal in this phase is the 12 exact duplicates in bank-additional-full.csv.

## Track A: churn_clean.csv

**last_transaction.** 3,223 rows (11.4%) held the literal text "NaT" rather than a real missing value, a known artifact of writing a datetime column to CSV with pandas' own null marker and reading it back as plain text. These were converted to true missing values, then the column was parsed as a date. After conversion, 25,159 rows have a valid parsed date and 3,223 are missing. No additional rows failed to parse beyond the ones already flagged as "NaT" strings.

**dependents.** Five rows held values of 25, 32, 36, 50, and 52, against a plausible range of 0 to 9 for the rest of the column, with an unexplained gap between 9 and 25. These rows were checked against age, vintage, and occupation for signs of a column shift or data entry error; no pattern was found that would justify reconstructing an intended value. They were set to missing rather than capped or guessed at. `dependents` is now missing for 2,468 rows total (8.68% from the original file, plus these 5).

**age.** 806 rows (2.8%) show an age under 18, including 4 rows with age 1 to 5. No documentation in the source file confirms or rules out custodial or minor-held accounts, and "student" is a valid occupation category that is not limited to minors. Rather than deleting these rows without justification, they are kept in the cleaned file and marked with `age_under_18_flag`. Anyone doing age-based analysis downstream can decide whether to include them, rather than have that decision made silently here.

**customer_id.** Confirmed unique after cleaning (28,382 unique values across 28,382 rows). This remains the primary key for Track A.

No transformation was applied to the balance or credit/debit columns in this phase. Their right-skewed distributions (documented in DATA_AUDIT.md) are a modeling concern, not a data quality defect, so any log transform or winsorization is left to whoever builds features from this data, not applied silently during cleaning.

## Track B: bank_additional_clean.csv (primary) and bank_full_clean.csv (secondary)

**Duplicates.** bank-additional-full.csv contained 12 exact duplicate rows across all 21 original columns, confirmed independently in this phase. They were removed with `drop_duplicates()`, bringing the row count from 41,188 to 41,176. bank-full.csv contains no exact duplicate rows.

**pdays sentinel.** Both files use a numeric value to mean "never contacted before": 999 in bank-additional-full.csv, -1 in bank-full.csv. Left as a raw number, this sentinel would distort any mean, correlation, or regression involving `pdays`. Both cleaned files now carry `previous_contact_flag` (boolean) and `days_since_previous_contact` (numeric, missing where the flag is false). In bank-additional-full.csv, 1,515 rows (3.68%) were previously contacted; in bank-full.csv, 8,257 rows (18.26%) were. This is a genuine difference between the two extracts, not a cleaning artifact.

**"unknown" categorical values.** Both files use the string "unknown" as a missing-value marker inside otherwise valid categorical columns. Frequencies, computed directly from the cleaned data:

| Column | bank_additional_clean.csv | bank_full_clean.csv |
|---|---:|---:|
| job | 0.80% | 0.64% |
| marital | 0.19% | not present |
| education | 4.20% | 4.11% |
| default | 20.88% | not present as "unknown" |
| housing | 2.40% | not present |
| loan | 2.40% | not present |
| contact | not present | 28.80% |
| poutcome | uses "nonexistent" instead | 81.75% |

**Decision:** "unknown" is retained as its own explicit category in both cleaned files rather than imputed to the mode or dropped. Non-disclosure is itself informative, particularly for `default` at nearly 21% and `poutcome`/`contact` at well over a quarter of rows in bank-full.csv. Replacing that many rows with a guessed mode value would manufacture certainty the data does not support. Anyone doing a chi-square test or building a model on these columns should treat "unknown" as a real level, not drop it.

**duration.** Retained in both cleaned files unchanged. It is not deleted, because it remains useful for descriptive statistics and for an explicit benchmark comparison showing what including it would do to a model. It must never be used as a pre-contact prediction feature. This exclusion is enforced in code, not just documentation: see `src/data/feature_config.py`, where `MODEL_READY_FEATURES` excludes `duration` by construction. Full reasoning in `docs/DATA_LEAKAGE.md`.

## Date limitations

Neither marketing file contains a year, even though the campaign spans May 2008 to November 2010 per the source documentation. No year was invented or assumed. `month` and `day` (bank-full.csv) or `day_of_week` (bank-additional-full.csv) are preserved as separate fields, and no calendar-date column was created for either file. Any month-over-month analysis will need to be described explicitly as relative/seasonal, not tied to a specific year.

For churn_clean.csv, `last_transaction` is a genuine calendar date and was parsed as one; this limitation does not apply to Track A.

## Validation

`src/data/validate.py` checks, after cleaning: row counts against the numbers in the table above, `customer_id` uniqueness and non-null status in Track A, target values restricted to the expected set in both tracks, no duplicate rows remaining in bank_additional_clean.csv, no literal "NaT" strings remaining in `last_transaction`, `dependents` capped at 9, presence of `previous_contact_flag` and `days_since_previous_contact` with sentinel values correctly excluded from the latter, and presence of `duration` (confirming it was retained, not silently dropped). All checks passed on the current run.

Result on the cleaned data: churn rate 18.53%, bank_additional_clean.csv target yes-rate 11.27%, bank_full_clean.csv target yes-rate 11.70%. These match the raw-file figures in DATA_AUDIT.md within rounding, as expected since cleaning did not change the target distribution.
