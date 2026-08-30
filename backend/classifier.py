"""
Defensibility classifier for DisputeShield.

The model is trained only on train.csv and evaluated only on
the held-out test.csv.

Metrics reported:
- Precision
- Recall
- ROC-AUC
- False-positive rate
- Confusion matrix
- False-positive cost
- Recovered transaction value
- Net modeled value
"""

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


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


# Illustrative assumptions.
# These are not measured Razorpay figures.
COST_PER_FALSE_POSITIVE_INR = 550
VALUE_PER_TRUE_POSITIVE_INR_MULTIPLIER = 1.0


@dataclass
class EvalResult:
    precision: float
    recall: float
    roc_auc: float
    false_positive_rate: float
    confusion: dict
    total_false_positive_cost_inr: float
    total_recovered_value_inr: float
    net_value_inr: float
    n_train: int
    n_test: int


def _prep_features(df: pd.DataFrame) -> pd.DataFrame:

    X = df[FEATURE_COLS].copy()

    boolean_cols = [
        "delivery_confirmed",
        "tracking_matches_address",
        "signed_delivery_proof",
        "device_matches_prior_orders",
        "ip_geo_matches_billing",
        "support_ticket_exists",
        "duplicate_txn_id_found",
        "subscription_cancel_logged",
    ]

    for col in boolean_cols:
        X[col] = X[col].astype(int)

    reason_dummies = pd.get_dummies(
        df["reason_code"],
        prefix=REASON_DUMMY_PREFIX
    )

    return pd.concat(
        [X, reason_dummies],
        axis=1
    )


def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    model_out_path: str,
) -> EvalResult:

    X_train = _prep_features(train_df)
    X_test = _prep_features(test_df)

    y_train = (
        train_df["outcome"] == "won"
    ).astype(int)

    y_test = (
        test_df["outcome"] == "won"
    ).astype(int)

    amounts_test = test_df["amount_inr"].values


    # Make sure train and test have identical feature columns.

    X_test = X_test.reindex(
        columns=X_train.columns,
        fill_value=0
    )


    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=5,
        random_state=7
    )

    clf.fit(
        X_train,
        y_train
    )


    y_pred = clf.predict(
        X_test
    )

    y_proba = clf.predict_proba(
        X_test
    )[:, 1]


    precision = precision_score(
        y_test,
        y_pred
    )

    recall = recall_score(
        y_test,
        y_pred
    )

    auc = roc_auc_score(
        y_test,
        y_proba
    )


    tn, fp, fn, tp = confusion_matrix(
        y_test,
        y_pred
    ).ravel()


    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0
    )


    fp_cost = (
        int(fp)
        * COST_PER_FALSE_POSITIVE_INR
    )


    recovered_value = float(
        np.sum(
            amounts_test[
                (y_pred == 1)
                & (y_test.values == 1)
            ]
        )
        * VALUE_PER_TRUE_POSITIVE_INR_MULTIPLIER
    )


    net_value = (
        recovered_value
        - fp_cost
    )


    # Save trained model and exact feature schema.

    joblib.dump(
        {
            "model": clf,
            "feature_cols": list(X_train.columns),
        },
        model_out_path
    )


    return EvalResult(

        precision=round(
            float(precision),
            3
        ),

        recall=round(
            float(recall),
            3
        ),

        roc_auc=round(
            float(auc),
            3
        ),

        false_positive_rate=round(
            float(false_positive_rate),
            3
        ),

        confusion={
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },

        total_false_positive_cost_inr=round(
            fp_cost,
            2
        ),

        total_recovered_value_inr=round(
            recovered_value,
            2
        ),

        net_value_inr=round(
            net_value,
            2
        ),

        n_train=len(y_train),
        n_test=len(y_test),
    )


def score_single(
    model_bundle: dict,
    row: pd.Series
) -> tuple[str, float]:

    X = _prep_features(
        pd.DataFrame([row])
    )


    for col in model_bundle["feature_cols"]:

        if col not in X.columns:
            X[col] = 0


    X = X[
        model_bundle["feature_cols"]
    ]


    proba = model_bundle[
        "model"
    ].predict_proba(X)[0, 1]


    label = (
        "winnable"
        if proba >= 0.5
        else "not_winnable"
    )


    return (
        label,
        round(float(proba), 3)
    )


if __name__ == "__main__":

    DATA_DIR = (
        Path(__file__).resolve().parent.parent
        / "data"
    )


    train_df = pd.read_csv(
        DATA_DIR / "train.csv"
    )

    test_df = pd.read_csv(
        DATA_DIR / "test.csv"
    )


    result = train_and_evaluate(
        train_df,
        test_df,
        str(DATA_DIR / "model.joblib")
    )


    print("\n========================================")
    print("       DISPUTESHIELD MODEL EVALUATION")
    print("========================================")

    print("\nDataset")
    print("----------------------------------------")
    print(f"Training cases:     {result.n_train}")
    print(f"Held-out test:      {result.n_test}")

    print("\nClassification Metrics")
    print("----------------------------------------")
    print(f"Precision:           {result.precision:.1%}")
    print(f"Recall:              {result.recall:.1%}")
    print(f"ROC-AUC:             {result.roc_auc:.1%}")
    print(
        f"False-positive rate: {result.false_positive_rate:.1%}"
    )

    print("\nConfusion Matrix")
    print("----------------------------------------")
    print(f"True negatives:      {result.confusion['tn']}")
    print(f"False positives:     {result.confusion['fp']}")
    print(f"False negatives:     {result.confusion['fn']}")
    print(f"True positives:      {result.confusion['tp']}")

    print("\nBusiness Impact")
    print("----------------------------------------")
    print(
        f"False-positive cost: "
        f"₹{result.total_false_positive_cost_inr:,.2f}"
    )
    print(
        f"Recovered value:     "
        f"₹{result.total_recovered_value_inr:,.2f}"
    )
    print(
        f"Net modeled value:   "
        f"₹{result.net_value_inr:,.2f}"
    )

    print("\nAssumption")
    print("----------------------------------------")
    print(
        "₹550 per false positive "
        "(illustrative operational + admin cost)"
    )

    print("\nModel saved to:")
    print(DATA_DIR / "model.joblib")