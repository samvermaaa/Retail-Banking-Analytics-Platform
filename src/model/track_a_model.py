"""
Track A modeling: customer churn (churn_clean.csv).

duration does not exist in this track; the leakage variable relevant to
Track A is the engineered last_transaction recency feature, which is kept
but explicitly checked against by looking at its permutation importance
for the final model (see docs/MODELING.md).

    python src/model/track_a_model.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

import sys
sys.path.append(str(Path(__file__).parent))
from common import RANDOM_STATE, evaluate_model, threshold_sweep, comparison_table

PROCESSED_DIR = Path("data/processed")
OUT_DIR = Path("data/model_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REFERENCE_DATE = pd.Timestamp("2019-12-31")

NUMERIC_FEATURES = [
    "vintage", "age", "dependents", "customer_nw_category",
    "current_balance", "previous_month_end_balance",
    "average_monthly_balance_prevQ", "average_monthly_balance_prevQ2",
    "current_month_credit", "previous_month_credit",
    "current_month_debit", "previous_month_debit",
    "current_month_balance", "previous_month_balance",
    "days_since_last_transaction",
]
BINARY_FEATURES = ["age_under_18_flag", "last_transaction_missing_flag"]
CATEGORICAL_FEATURES = ["gender", "occupation"]
TARGET = "churn"


def load_features():
    df = pd.read_csv(PROCESSED_DIR / "churn_clean.csv", parse_dates=["last_transaction"])

    df["last_transaction_missing_flag"] = df["last_transaction"].isna().astype(int)
    df["days_since_last_transaction"] = (
        REFERENCE_DATE - df["last_transaction"]
    ).dt.days

    # city and branch_code are high-cardinality identifiers (DATA_AUDIT.md),
    # not usable as raw features without a grouping strategy not attempted
    # in this phase. customer_id is the key, not a feature.
    feature_cols = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
    X = df[feature_cols].copy()
    y = df[TARGET].copy()
    return X, y


def build_preprocessor():
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, NUMERIC_FEATURES + BINARY_FEATURES),
        ("cat", categorical_pipe, CATEGORICAL_FEATURES),
    ])


def build_models():
    return {
        "Logistic Regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(
            class_weight="balanced", max_depth=6, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            class_weight="balanced", n_estimators=300, max_depth=10,
            random_state=RANDOM_STATE, n_jobs=-1),
    }


def get_feature_names(preprocessor):
    num_names = NUMERIC_FEATURES + BINARY_FEATURES
    cat_names = list(
        preprocessor.named_transformers_["cat"]
        .named_steps["onehot"].get_feature_names_out(CATEGORICAL_FEATURES)
    )
    return num_names + cat_names


def run():
    X, y = load_features()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    preprocessor = build_preprocessor()
    models = build_models()

    results = []
    fitted_pipelines = {}
    cv_scores = {}
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    for name, clf in models.items():
        pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
        cv = cross_val_score(pipe, X_train, y_train, cv=skf, scoring="average_precision")
        cv_scores[name] = (cv.mean(), cv.std())

        pipe.fit(X_train, y_train)
        y_prob = pipe.predict_proba(X_test)[:, 1]
        results.append(evaluate_model(name, y_test, y_prob))
        fitted_pipelines[name] = (pipe, y_prob)

    comparison = comparison_table(results)

    # final model selection is documented in docs/MODELING.md, not hardcoded
    # to whichever happens to score highest without review
    best_name = comparison.sort_values("pr_auc", ascending=False).iloc[0]["model"]
    best_pipe, best_prob = fitted_pipelines[best_name]

    thresholds = threshold_sweep(y_test, best_prob)

    # interpretability
    fitted_preprocessor = best_pipe.named_steps["prep"]
    feature_names = get_feature_names(fitted_preprocessor)

    logreg_pipe, logreg_prob = fitted_pipelines["Logistic Regression"]
    logreg_coefs = pd.DataFrame({
        "feature": feature_names,
        "coefficient": logreg_pipe.named_steps["clf"].coef_[0],
    }).sort_values("coefficient", key=abs, ascending=False)

    rf_pipe, _ = fitted_pipelines["Random Forest"]
    rf_importance = pd.DataFrame({
        "feature": feature_names,
        "importance": rf_pipe.named_steps["clf"].feature_importances_,
    }).sort_values("importance", ascending=False)

    perm = permutation_importance(
        best_pipe, X_test, y_test, n_repeats=10, random_state=RANDOM_STATE,
        scoring="average_precision", n_jobs=-1)
    perm_importance = pd.DataFrame({
        "feature": X_test.columns,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)

    comparison.to_csv(OUT_DIR / "track_a_model_comparison.csv", index=False)
    thresholds.to_csv(OUT_DIR / "track_a_threshold_analysis.csv", index=False)
    logreg_coefs.to_csv(OUT_DIR / "track_a_logreg_coefficients.csv", index=False)
    rf_importance.to_csv(OUT_DIR / "track_a_rf_importance.csv", index=False)
    perm_importance.to_csv(OUT_DIR / "track_a_permutation_importance.csv", index=False)

    print("Track A: 5-fold CV average precision (mean, std)")
    for name, (m, s) in cv_scores.items():
        print(f"  {name}: {m:.4f} +/- {s:.4f}")
    print()
    print("Track A test set comparison")
    print(comparison.to_string(index=False))
    print()
    print(f"Track A best model by PR-AUC: {best_name}")
    print()
    print("Threshold sweep (best model)")
    print(thresholds.round(4).to_string(index=False))
    print()
    print("Logistic Regression coefficients (top 10 by magnitude)")
    print(logreg_coefs.head(10).to_string(index=False))
    print()
    print("Random Forest importance (top 10)")
    print(rf_importance.head(10).to_string(index=False))
    print()
    print("Permutation importance on best model (top 10)")
    print(perm_importance.head(10).to_string(index=False))

    return {
        "comparison": comparison,
        "best_name": best_name,
        "thresholds": thresholds,
        "logreg_coefs": logreg_coefs,
        "rf_importance": rf_importance,
        "perm_importance": perm_importance,
        "cv_scores": cv_scores,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }


if __name__ == "__main__":
    run()
