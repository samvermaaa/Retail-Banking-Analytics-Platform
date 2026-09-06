"""
Validation for the cleaned analytical datasets. Run after clean.py.

Exits with a non-zero status and a printed list of failures if any check
fails. Does not just print a success message without checking anything.

    python src/data/validate.py
"""

import sys
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def validate_churn():
    df = pd.read_csv(PROCESSED_DIR / "churn_clean.csv")

    check(len(df) == 28382, f"churn_clean.csv row count changed unexpectedly: {len(df)}")
    check(set(df.columns) >= {
        "customer_id", "vintage", "age", "gender", "dependents", "occupation",
        "city", "customer_nw_category", "branch_code", "current_balance",
        "churn", "last_transaction", "age_under_18_flag",
    }, "churn_clean.csv is missing an expected column")
    check(df["customer_id"].is_unique, "customer_id is not unique in churn_clean.csv")
    check(df["customer_id"].isna().sum() == 0, "customer_id has missing values")
    check(df["churn"].dropna().isin([0, 1]).all(), "churn contains values outside {0, 1}")
    check((df["dependents"].dropna() <= 9).all(), "dependents still contains values above the plausible cap")
    check(df["last_transaction"].apply(lambda x: x != "NaT").all(),
          "literal 'NaT' string still present in last_transaction")
    check(df["age_under_18_flag"].dtype == bool, "age_under_18_flag is not boolean")

    balance_cols = [c for c in df.columns if "balance" in c]
    for c in balance_cols:
        check(df[c].isna().sum() == 0, f"unexpected missing values in {c}")

    return {
        "rows": len(df),
        "churn_rate": round(float(df["churn"].mean()), 4),
        "missing_dependents": int(df["dependents"].isna().sum()),
        "missing_last_transaction": int(df["last_transaction"].isna().sum()),
    }


def validate_marketing(path, expected_rows, sentinel_removed_value, name):
    df = pd.read_csv(PROCESSED_DIR / path)

    check(len(df) == expected_rows, f"{name} row count is {len(df)}, expected {expected_rows}")
    check(df.duplicated().sum() == 0, f"{name} still contains exact duplicate rows")
    check(df["y"].dropna().isin(["yes", "no"]).all(), f"{name} target y has unexpected values")
    check("previous_contact_flag" in df.columns, f"{name} is missing previous_contact_flag")
    check(sentinel_removed_value not in df.loc[df["previous_contact_flag"], "pdays"].unique() if
          df["previous_contact_flag"].any() else True,
          f"{name} sentinel value leaked into previous_contact_flag=True rows")
    check(df.loc[~df["previous_contact_flag"], "days_since_previous_contact"].isna().all(),
          f"{name} days_since_previous_contact should be missing where previous_contact_flag is False")
    check("duration" in df.columns, f"{name} is missing duration (should be retained, not deleted)")

    return {
        "rows": len(df),
        "target_yes_rate": round(float((df["y"] == "yes").mean()), 4),
        "previously_contacted_rate": round(float(df["previous_contact_flag"].mean()), 4),
    }


if __name__ == "__main__":
    import json

    summary = {}
    summary["churn"] = validate_churn()
    summary["bank_additional"] = validate_marketing(
        "bank_additional_clean.csv", 41176, 999, "bank_additional_clean.csv")
    summary["bank_full"] = validate_marketing(
        "bank_full_clean.csv", 45211, -1, "bank_full_clean.csv")

    print(json.dumps(summary, indent=2))

    if failures:
        print("\nVALIDATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\nAll checks passed.")
