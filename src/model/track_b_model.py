"""
Track B modeling: product adoption (bank_additional_clean.csv, primary dataset).

Features come from src/data/feature_config.py MODEL_READY_FEATURES, which
already excludes duration. This script does not read duration from the
CSV at all, so it cannot be accidentally reintroduced through a derived
feature.

    python src/model/track_b_model.py
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
sys.path.append(str(Path(__file__).parent.parent / "data"))
from common import RANDOM_STATE, evaluate_model, threshold_sweep, comparison_table
from feature_config import MODEL_READY_FEATURES, TARGET, LEAKAGE_FEATURES

PROCESSED_DIR = Path("data/processed")
OUT_DIR = Path("data/model_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUMERIC_FEATURES = [
    "age", "campaign", "days_since_previous_contact", "previous",
    "emp.var.rate", "cons.price.idx", "cons.conf.idx", "euribor3m",
    "nr.employed",
]
BINARY_FEATURES = ["previous_contact_flag"]
CATEGORICAL_FEATURES = [
    "job", "marital", "education", "default", "housing", "loan",
    "contact", "month", "day_of_week", "poutcome",
]


def load_features():
    df = pd.read_csv(PROCESSED_DIR / "bank_additional_clean.csv")

    assert set(MODEL_READY_FEATURES) == set(
        NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
    ), "feature list here has drifted from feature_config.py"
    assert "duration" not in (NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES)
    for f in LEAKAGE_FEATURES:
        assert f not in (NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES)

    X = df[MODEL_READY_FEATURES].copy()
    y = (df[TARGET] == "yes").astype(int)
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

    best_name = comparison.sort_values("pr_auc", ascending=False).iloc[0]["model"]
    best_pipe, best_prob = fitted_pipelines[best_name]

    thresholds = threshold_sweep(y_test, best_prob)

    fitted_preprocessor = best_pipe.named_steps["prep"]
    feature_names = get_feature_names(fitted_preprocessor)

    logreg_pipe, _ = fitted_pipelines["Logistic Regression"]
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

    comparison.to_csv(OUT_DIR / "track_b_model_comparison.csv", index=False)
    thresholds.to_csv(OUT_DIR / "track_b_threshold_analysis.csv", index=False)
    logreg_coefs.to_csv(OUT_DIR / "track_b_logreg_coefficients.csv", index=False)
    rf_importance.to_csv(OUT_DIR / "track_b_rf_importance.csv", index=False)
    perm_importance.to_csv(OUT_DIR / "track_b_permutation_importance.csv", index=False)

    print("Track B: 5-fold CV average precision (mean, std)")
    for name, (m, s) in cv_scores.items():
        print(f"  {name}: {m:.4f} +/- {s:.4f}")
    print()
    print("Track B test set comparison")
    print(comparison.to_string(index=False))
    print()
    print(f"Track B best model by PR-AUC: {best_name}")
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
        "n_train": len(X_train),
        "n_test": len(X_test),
    }


if __name__ == "__main__":
    run()
