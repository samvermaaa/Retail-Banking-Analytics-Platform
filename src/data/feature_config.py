"""
Feature configuration for Track B (campaign and product adoption).

This is the enforced boundary between descriptive/benchmark use of the
cleaned marketing data and any pre-contact prediction feature set. Agent 2
should import MODEL_READY_FEATURES rather than reading columns directly off
the cleaned CSV, so the leakage exclusion cannot be silently skipped.
"""

# duration is known only once a call has happened or ended, and the source
# documentation for bank-additional-full.csv states directly that it should
# not be used for a realistic pre-contact model. See docs/DATA_LEAKAGE.md.
LEAKAGE_FEATURES = ["duration"]

TARGET = "y"

BANK_ADDITIONAL_RAW_FEATURES = [
    "age", "job", "marital", "education", "default", "housing", "loan",
    "contact", "month", "day_of_week", "duration", "campaign",
    "previous_contact_flag", "days_since_previous_contact", "previous",
    "poutcome", "emp.var.rate", "cons.price.idx", "cons.conf.idx",
    "euribor3m", "nr.employed",
]

MODEL_READY_FEATURES = [
    f for f in BANK_ADDITIONAL_RAW_FEATURES if f not in LEAKAGE_FEATURES
]
