"""
DisputeShield Classifier & ML Evaluation Benchmark Suite (Version 2.1 - Leakage-Free)

Trained on train.csv (60%), threshold tuned on val.csv (20%), and evaluated strictly on held-out test.csv (20%).

Fixes:
1. Eliminates Test Set Threshold Leakage by performing optimal threshold selection strictly on Validation set.
2. Realistic Fintech Business Net Value Formula:
   - Includes Operational Filing/Review Cost (INR 150 per contested case).
   - Includes False Positive Administrative Fee (INR 550 per FP case).
   - Penalizes mindless 100% contestation with Card Brand Dispute Monitoring Surcharges if FP Rate > 15%.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from backend.config import settings, DATA_DIR

FEATURE_COLS = [
    "amount_inr",
    "delivery_confirmed",
    "tracking_matches_address",
    "signed_delivery_proof",
    "device_matches_prior_orders",
    "ip_geo_matches_billing",
    "customer_prior_clean_orders",
    "support_ticket_exists",
    "duplicate_txn_id_found",
    "subscription_cancel_logged",
    "days_since_transaction",
]

REASON_DUMMY_PREFIX = "reason_"
OPERATIONAL_REVIEW_COST_INR = 150.0  # Cost per contested case review
FP_PENALTY_SURCHARGE_INR = 1000.0   # Surcharge if FP rate exceeds 15% threshold


def _prep_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURE_COLS].copy()
    boolean_cols = [
        "delivery_confirmed", "tracking_matches_address", "signed_delivery_proof",
        "device_matches_prior_orders", "ip_geo_matches_billing", "support_ticket_exists",
        "duplicate_txn_id_found", "subscription_cancel_logged"
    ]
    for col in boolean_cols:
        if col in X.columns:
            X[col] = X[col].astype(int)

    reason_dummies = pd.get_dummies(df["reason_code"], prefix=REASON_DUMMY_PREFIX)
    return pd.concat([X, reason_dummies], axis=1)


def evaluate_rules_baseline(test_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Heuristic rule-only prediction baseline."""
    preds = []
    probas = []
    for _, row in test_df.iterrows():
        score = 0.5
        reason = row.get("reason_code", "")
        if reason == "item_not_received":
            score = 0.85 if row.get("signed_delivery_proof") else (0.65 if row.get("delivery_confirmed") else 0.20)
        elif reason == "duplicate_charge":
            score = 0.90 if row.get("duplicate_txn_id_found") else 0.10
        elif reason == "subscription_cancelled":
            score = 0.85 if row.get("subscription_cancel_logged") else 0.15
        elif reason == "unrecognized_transaction":
            score = 0.80 if (row.get("device_matches_prior_orders") and row.get("ip_geo_matches_billing")) else 0.20
        else:
            score = 0.50
        probas.append(score)
        preds.append(1 if score >= 0.5 else 0)
    return np.array(preds), np.array(probas)


def compute_metrics(model_name: str, y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray, amounts: np.ndarray) -> Dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    try:
        auc = roc_auc_score(y_true, y_proba)
    except Exception:
        auc = 0.5
        
    brier = brier_score_loss(y_true, y_proba)
    
    # Financial metrics including operational review cost & FP monitoring penalty
    n_contested = int(tp + fp)
    fp_rate = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    
    fp_cost = float(fp * settings.FALSE_POSITIVE_COST_INR)
    review_cost = float(n_contested * OPERATIONAL_REVIEW_COST_INR)
    penalty_cost = float(fp * FP_PENALTY_SURCHARGE_INR) if fp_rate > 0.15 else 0.0
    
    total_cost = fp_cost + review_cost + penalty_cost
    recovered_val = float(np.sum(amounts[(y_pred == 1) & (y_true == 1)]))
    net_val = recovered_val - total_cost

    return {
        "model_name": model_name,
        "precision": round(float(prec), 3),
        "recall": round(float(rec), 3),
        "f1_score": round(float(f1), 3),
        "roc_auc": round(float(auc), 3),
        "brier_score": round(float(brier), 3),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "contested_cases": n_contested,
        "false_positive_cost_inr": round(fp_cost, 2),
        "operational_review_cost_inr": round(review_cost, 2),
        "penalty_surcharge_inr": round(penalty_cost, 2),
        "recovered_value_inr": round(recovered_val, 2),
        "net_value_inr": round(net_val, 2)
    }


def find_optimal_threshold_on_val(y_val: np.ndarray, y_proba_val: np.ndarray, amounts_val: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Sweep threshold t in [0.10, 0.90] strictly on VALIDATION set probabilities.
    Prevents test set threshold leakage.
    """
    best_threshold = 0.50
    best_net_value = -float("inf")
    threshold_results = []

    for t in np.linspace(0.10, 0.90, 81):
        t = round(float(t), 2)
        y_pred = (y_proba_val >= t).astype(int)
        
        metrics = compute_metrics("val_sweep", y_val, y_pred, y_proba_val, amounts_val)
        net_val = metrics["net_value_inr"]

        if net_val > best_net_value:
            best_net_value = net_val
            best_threshold = t

        threshold_results.append({
            "threshold": t,
            "net_val": net_val
        })

    return best_threshold, {
        "optimal_threshold": best_threshold,
        "val_max_net_value_inr": best_net_value,
        "sweep_sample": threshold_results[::10]
    }


def train_and_benchmark() -> Dict[str, Any]:
    train_path = DATA_DIR / "train.csv"
    val_path = DATA_DIR / "val.csv"
    test_path = DATA_DIR / "test.csv"

    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        from backend.create_test_set import split_data
        split_data()

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    X_train = _prep_features(train_df)
    X_val = _prep_features(val_df)
    X_test = _prep_features(test_df)
    
    y_train = (train_df["outcome"] == "won").astype(int).values
    y_val = (val_df["outcome"] == "won").astype(int).values
    y_test = (test_df["outcome"] == "won").astype(int).values
    
    amounts_val = val_df["amount_inr"].values
    amounts_test = test_df["amount_inr"].values

    # Align feature columns
    X_val = X_val.reindex(columns=X_train.columns, fill_value=0)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    feature_cols = list(X_train.columns)

    benchmarks = {}

    # 1. Dummy Baseline (Majority Class)
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    dummy_pred = dummy.predict(X_test)
    dummy_proba = dummy.predict_proba(X_test)[:, 1]
    benchmarks["baseline_majority"] = compute_metrics("Majority Class Baseline", y_test, dummy_pred, dummy_proba, amounts_test)

    # 2. Rules-Only Baseline
    rules_pred, rules_proba = evaluate_rules_baseline(test_df)
    benchmarks["baseline_rules"] = compute_metrics("Heuristic Rules Baseline", y_test, rules_pred, rules_proba, amounts_test)

    # 3. Logistic Regression (Standardized)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    lr = LogisticRegression(max_iter=2000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    lr_pred = lr.predict(X_test_scaled)
    lr_proba = lr.predict_proba(X_test_scaled)[:, 1]
    benchmarks["logistic_regression"] = compute_metrics("Logistic Regression", y_test, lr_pred, lr_proba, amounts_test)

    # 4. RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=5, random_state=42)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_proba = rf.predict_proba(X_test)[:, 1]
    benchmarks["random_forest"] = compute_metrics("Random Forest", y_test, rf_pred, rf_proba, amounts_test)

    # 5. Calibrated GradientBoostingClassifier (Production Model)
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    calibrated_gb = CalibratedClassifierCV(estimator=gb, method="sigmoid", cv=3)
    calibrated_gb.fit(X_train, y_train)
    
    gb_proba_val = calibrated_gb.predict_proba(X_val)[:, 1]
    gb_proba_test = calibrated_gb.predict_proba(X_test)[:, 1]

    # Find optimal threshold ON VALIDATION SET ONLY
    opt_threshold, val_opt_info = find_optimal_threshold_on_val(y_val, gb_proba_val, amounts_val)

    # Apply validation-derived threshold to held-out test predictions
    gb_pred_test_opt = (gb_proba_test >= opt_threshold).astype(int)
    benchmarks["gradient_boosting_calibrated"] = compute_metrics("Calibrated Gradient Boosting", y_test, gb_pred_test_opt, gb_proba_test, amounts_test)

    # Save Model Artifact
    joblib.dump(
        {
            "model": calibrated_gb,
            "feature_cols": feature_cols,
            "version": "gb_calibrated_v2.1",
            "optimal_threshold": opt_threshold
        },
        settings.MODEL_PATH
    )

    evaluation_report = {
        "model_version": "gb_calibrated_v2.1",
        "n_train": len(y_train),
        "n_val": len(y_val),
        "n_test": len(y_test),
        "optimal_threshold": opt_threshold,
        "validation_sweep": val_opt_info,
        "primary_model_metrics": benchmarks["gradient_boosting_calibrated"],
        "benchmarks": benchmarks
    }

    with open(settings.METRICS_PATH, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    return evaluation_report


def score_single_dispute(model_bundle: dict, row: pd.Series) -> Tuple[str, float]:
    X = _prep_features(pd.DataFrame([row]))
    for col in model_bundle["feature_cols"]:
        if col not in X.columns:
            X[col] = 0
    X = X[model_bundle["feature_cols"]]

    proba = float(model_bundle["model"].predict_proba(X)[0, 1])
    label = "winnable" if proba >= model_bundle.get("optimal_threshold", 0.50) else "not_winnable"
    return label, round(proba, 4)


if __name__ == "__main__":
    print("Running Leakage-Free ML Benchmark Suite...")
    results = train_and_benchmark()
    print("Benchmark complete. Metrics saved to data/evaluation_metrics.json.")
    print("Primary Model (Calibrated Gradient Boosting) Metrics on Unseen Test Set:")
    print(f"ROC-AUC: {results['primary_model_metrics']['roc_auc']:.1%}")
    print(f"Brier Score: {results['primary_model_metrics']['brier_score']}")
    print(f"Validation-Derived Optimal Threshold: {results['optimal_threshold']}")
    print(f"Net Recovered Value: INR {results['primary_model_metrics']['net_value_inr']:,.2f}")