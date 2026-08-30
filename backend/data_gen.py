"""
Synthetic chargeback-dispute dataset generator.

Simulates what Razorpay test-mode transaction + delivery + support-comms
data would look like for disputed transactions. Each row is one disputed
transaction with the evidence signals a real evidence-response pipeline
would pull, plus a ground-truth label of whether the dispute was
winnable (outcome == "won") based on a hand-specified, documented rule
set (this stands in for real historical outcome labels; swap in real
labeled data when available).
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RNG = np.random.default_rng(42)

REASON_CODES = [
    "item_not_received",
    "item_not_as_described",
    "duplicate_charge",
    "unrecognized_transaction",
    "subscription_cancelled",
]


def _sample_row(i: int) -> dict:
    reason = RNG.choice(REASON_CODES, p=[0.35, 0.15, 0.15, 0.25, 0.10])

    delivery_confirmed = RNG.random() < 0.62
    tracking_matches_address = delivery_confirmed and RNG.random() < 0.9
    device_matches_prior_orders = RNG.random() < 0.7
    ip_geo_matches_billing = RNG.random() < 0.75
    customer_has_prior_clean_orders = RNG.integers(0, 12)
    support_ticket_exists = RNG.random() < 0.4
    signed_delivery_proof = delivery_confirmed and RNG.random() < 0.55
    days_since_transaction = int(RNG.integers(1, 120))
    amount_inr = float(np.round(RNG.gamma(2.0, 800), 2))
    duplicate_txn_id_found = reason == "duplicate_charge" and RNG.random() < 0.8
    subscription_cancel_logged = reason == "subscription_cancelled" and RNG.random() < 0.45

    # --- Documented ground-truth rule (stand-in for real historical labels) ---
    score = 0
    if reason == "item_not_received":
        score += 3 if signed_delivery_proof else (1 if delivery_confirmed else -2)
        score += 1 if tracking_matches_address else 0
    elif reason == "item_not_as_described":
        score += 1 if support_ticket_exists else -1
    elif reason == "duplicate_charge":
        score += 3 if duplicate_txn_id_found else -3
    elif reason == "unrecognized_transaction":
        score += 2 if (device_matches_prior_orders and ip_geo_matches_billing) else -2
        score += 1 if customer_has_prior_clean_orders >= 3 else 0
    elif reason == "subscription_cancelled":
        score += 3 if subscription_cancel_logged else -3

    score += 1 if customer_has_prior_clean_orders >= 5 else 0
    score -= 1 if days_since_transaction > 90 else 0

    # winnable if net evidence score clears a threshold; add noise for realism
    p_win = 1 / (1 + np.exp(-(score - 0.5)))
    outcome = "won" if RNG.random() < p_win else "lost"

    return {
        "transaction_id": f"TXN{100000 + i}",
        "reason_code": reason,
        "amount_inr": amount_inr,
        "delivery_confirmed": delivery_confirmed,
        "tracking_matches_address": tracking_matches_address,
        "signed_delivery_proof": signed_delivery_proof,
        "device_matches_prior_orders": device_matches_prior_orders,
        "ip_geo_matches_billing": ip_geo_matches_billing,
        "customer_prior_clean_orders": int(customer_has_prior_clean_orders),
        "support_ticket_exists": support_ticket_exists,
        "duplicate_txn_id_found": duplicate_txn_id_found,
        "subscription_cancel_logged": subscription_cancel_logged,
        "days_since_transaction": days_since_transaction,
        "outcome": outcome,  # ground truth label: "won" / "lost"
    }


def generate_supporting_tables(df):

    transactions = df[
        [
            "transaction_id",
            "amount_inr"
        ]
    ]

    delivery = df[
        [
            "transaction_id",
            "delivery_confirmed",
            "tracking_matches_address",
            "signed_delivery_proof"
        ]
    ]

    support = df[
        [
            "transaction_id",
            "support_ticket_exists"
        ]
    ].copy()

    support["resolution"] = support["support_ticket_exists"].apply(
        lambda x: "customer_contacted" if x else "no_ticket"
    )

    transactions.to_csv(
        DATA_DIR / "transactions.csv",
        index=False
    )

    delivery.to_csv(
        DATA_DIR / "delivery.csv",
        index=False
    )

    support.to_csv(
        DATA_DIR / "support_logs.csv",
        index=False
    )


if __name__ == "__main__":

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Generate main dispute dataset
    df = pd.DataFrame(
        [_sample_row(i) for i in range(5000)]
    )
    print("Main dataframe:")
    print(df.head())
    print("Rows:", len(df))


    # Save complete disputes dataset
    df.to_csv(
        DATA_DIR / "disputes.csv",
        index=False
    )

    # Generate evidence source tables
    generate_supporting_tables(df)

    print("Generated:")
    print("✓ disputes.csv")
    print("✓ transactions.csv")
    print("✓ delivery.csv")
    print("✓ support_logs.csv")