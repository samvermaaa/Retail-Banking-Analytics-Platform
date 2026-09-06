"""
Cleaning pipeline for the two analytical tracks.

Track A: churn_prediction.csv -> data/processed/churn_clean.csv
Track B: bank-additional-full.csv -> data/processed/bank_additional_clean.csv
         bank-full.csv (secondary) -> data/processed/bank_full_clean.csv

Never modifies files under raw/. Run from the project root:

    python src/data/clean.py
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path("raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEPENDENTS_MAX_PLAUSIBLE = 9  # next observed value jumps to 25, an unexplained gap


def clean_churn():
    df = pd.read_csv(RAW_DIR / "churn/churn_prediction.csv")
    report = {"dataset": "churn_prediction.csv", "original_rows": len(df)}

    # last_transaction: the source file stores missing dates as the literal
    # string "NaT" (an artifact of a datetime column being exported to CSV
    # with pandas' own null marker and then re-read as text). That string
    # does not register as missing under isna(), so it has to be replaced
    # before parsing.
    nat_string_count = (df["last_transaction"] == "NaT").sum()
    df["last_transaction"] = df["last_transaction"].replace("NaT", pd.NA)
    df["last_transaction"] = pd.to_datetime(df["last_transaction"], errors="coerce")
    unparseable = df["last_transaction"].isna().sum() - nat_string_count
    report["last_transaction_nat_string_count"] = int(nat_string_count)
    report["last_transaction_unparseable_after_nat_fix"] = int(unparseable)
    report["last_transaction_valid_dates"] = int(df["last_transaction"].notna().sum())

    # dependents: six rows hold values of 25, 32, 36, 50 and 52. These rows
    # were checked against age, vintage and occupation and show no sign of a
    # column shift, so there is no basis for reconstructing an intended
    # value. They are treated as invalid and set to missing rather than
    # guessed at or capped to the plausible maximum.
    invalid_dependents = df["dependents"] > DEPENDENTS_MAX_PLAUSIBLE
    report["dependents_invalid_count"] = int(invalid_dependents.sum())
    df.loc[invalid_dependents, "dependents"] = pd.NA

    # age: 806 rows show an age under 18, including four rows with age 1 to
    # 5. The source has no documentation confirming custodial or minor
    # accounts, and occupation includes a "student" category that is not
    # restricted to minors, so there is no basis to treat these as errors
    # and delete them. They are kept and flagged so that any age-based
    # analysis can decide whether to include them.
    df["age_under_18_flag"] = df["age"] < 18
    report["age_under_18_count"] = int(df["age_under_18_flag"].sum())

    # customer_id must remain a unique key after all of the above.
    report["customer_id_unique_after_cleaning"] = bool(df["customer_id"].is_unique)
    report["final_rows"] = len(df)

    df.to_csv(OUT_DIR / "churn_clean.csv", index=False)
    return report


def clean_bank_additional():
    df = pd.read_csv(
        RAW_DIR / "marketing/bank-additional/bank-additional/bank-additional-full.csv",
        sep=";",
    )
    report = {"dataset": "bank-additional-full.csv", "original_rows": len(df)}

    duplicate_count = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    report["exact_duplicate_rows_removed"] = int(duplicate_count)
    report["rows_after_dedup"] = len(df)

    # pdays: 999 is a sentinel for "never contacted before," not a real day
    # count. Left as a raw number it would distort any mean or correlation
    # involving pdays. Split into an explicit flag plus a numeric field that
    # is only populated for clients who were actually contacted before.
    df["previous_contact_flag"] = df["pdays"] != 999
    df["days_since_previous_contact"] = df["pdays"].where(df["previous_contact_flag"])
    report["previously_contacted_count"] = int(df["previous_contact_flag"].sum())
    report["never_contacted_count"] = int((~df["previous_contact_flag"]).sum())

    # "unknown" categorical markers: kept as their own explicit category
    # rather than imputed. Non-disclosure is itself informative here (for
    # example, default is unknown for close to a fifth of rows), and mode
    # imputation would manufacture certainty that is not in the data.
    unknown_cols = [c for c in df.select_dtypes(include=["object","str"]).columns
                     if (df[c] == "unknown").any()]
    unknown_rates = {c: float((df[c] == "unknown").mean()) for c in unknown_cols}
    report["unknown_marker_columns"] = unknown_rates

    # duration is retained in the cleaned file for descriptive and benchmark
    # use, but it must never enter a pre-contact prediction feature set. See
    # src/data/feature_config.py for the enforced exclusion list, and
    # docs/DATA_LEAKAGE.md for the reasoning.
    report["duration_marked_leakage_for_prediction"] = True

    df.to_csv(OUT_DIR / "bank_additional_clean.csv", index=False)
    return report


def clean_bank_full():
    df = pd.read_csv(RAW_DIR / "marketing/bank/bank-full.csv", sep=";")
    report = {"dataset": "bank-full.csv", "original_rows": len(df)}

    duplicate_count = df.duplicated().sum()
    report["exact_duplicate_rows_found"] = int(duplicate_count)

    df["previous_contact_flag"] = df["pdays"] != -1
    df["days_since_previous_contact"] = df["pdays"].where(df["previous_contact_flag"])
    report["previously_contacted_count"] = int(df["previous_contact_flag"].sum())
    report["never_contacted_count"] = int((~df["previous_contact_flag"]).sum())

    unknown_cols = [c for c in df.select_dtypes(include=["object","str"]).columns
                     if (df[c] == "unknown").any()]
    unknown_rates = {c: float((df[c] == "unknown").mean()) for c in unknown_cols}
    report["unknown_marker_columns"] = unknown_rates
    report["duration_marked_leakage_for_prediction"] = True
    report["final_rows"] = len(df)

    df.to_csv(OUT_DIR / "bank_full_clean.csv", index=False)
    return report


if __name__ == "__main__":
    import json

    results = {
        "churn": clean_churn(),
        "bank_additional": clean_bank_additional(),
        "bank_full": clean_bank_full(),
    }
    print(json.dumps(results, indent=2, default=str))
