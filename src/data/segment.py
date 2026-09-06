"""
Customer segmentation for Track A (churn_prediction customers only).

Track B has no persistent customer identity (see DATA_AUDIT.md section 4.1),
so a "customer segmentation" is not methodologically meaningful there; this
script does not touch Track B.

The target variable (churn) is deliberately excluded from the feature set
to avoid target leakage into an unsupervised segmentation. customer_nw_category
and occupation are also excluded as inputs, since customer_nw_category is
already a bank-assigned tier and including it would partly reproduce an
existing label rather than discover a new one; both are used afterward for
profiling and validation instead.

    python src/data/segment.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score

PROCESSED_DIR = Path("data/processed")

FEATURE_COLS = [
    "vintage", "age", "current_balance",
    "average_monthly_balance_prevQ", "current_month_credit",
    "current_month_debit",
]

# current_balance and average_monthly_balance_prevQ can be negative, and all
# four monetary columns are heavily right-skewed with extreme outliers
# (DATA_AUDIT.md, finding 3.5). arcsinh compresses large magnitudes like a
# log transform but, unlike log1p, is defined for negative values too.
SKEWED_COLS = [
    "current_balance", "average_monthly_balance_prevQ",
    "current_month_credit", "current_month_debit",
]

FINAL_K = 4  # selected in docs/SEGMENTATION_DECISION.md


def build_features(df):
    X = df[FEATURE_COLS].copy()
    for c in SKEWED_COLS:
        X[c] = np.arcsinh(X[c])
    assert X.isna().sum().sum() == 0, "unexpected missing values in clustering features"
    return X


def evaluate_k_range(X_scaled, k_min=2, k_max=6):
    rows = []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels, sample_size=5000, random_state=42)
        db = davies_bouldin_score(X_scaled, labels)
        rows.append({
            "k": k,
            "silhouette": round(sil, 4),
            "davies_bouldin": round(db, 4),
            "cluster_sizes": pd.Series(labels).value_counts().sort_index().tolist(),
        })
    return pd.DataFrame(rows)


def fit_final(X_scaled, df):
    km = KMeans(n_clusters=FINAL_K, random_state=42, n_init=10)
    df = df.copy()
    df["segment"] = km.fit_predict(X_scaled)
    return df


def profile_segments(df):
    profile = df.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        avg_age=("age", "mean"),
        avg_vintage_days=("vintage", "mean"),
        avg_current_balance=("current_balance", "mean"),
        median_current_balance=("current_balance", "median"),
        avg_month_credit=("current_month_credit", "mean"),
        avg_month_debit=("current_month_debit", "mean"),
        churn_rate=("churn", "mean"),
    ).round(2)
    profile["pct_of_customers"] = (profile["customer_count"] / len(df) * 100).round(1)
    return profile


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_DIR / "churn_clean.csv")
    X = build_features(df)
    X_scaled = StandardScaler().fit_transform(X)

    k_eval = evaluate_k_range(X_scaled)
    print(k_eval.to_string(index=False))

    final_df = fit_final(X_scaled, df)
    profile = profile_segments(final_df)
    print()
    print(profile.to_string())

    final_df[["customer_id", "segment"]].to_csv(
        PROCESSED_DIR / "segment_assignments.csv", index=False)
    profile.to_csv(PROCESSED_DIR / "segment_profiles.csv")
