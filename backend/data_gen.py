"""
DisputeShield Synthetic Data Generator (Version 2.0)

Generates a realistic synthetic chargeback dataset simulating merchant transaction logs,
delivery signals, support interactions, and historical dispute outcomes.

Features realistic noise, unobserved latent variables, missing evidence fields,
contradictory signals, and temporal ordering to avoid synthetic tautology.

Documented Ground-Truth Generation Process:
1. Base score computed from domain-heuristic rules (evidence strength).
2. Unobserved latent fraud factor ~ Normal(0, 1.2) added (simulates real-world unknown fraud patterns).
3. Random noise (~15% flip probability) injected to represent issuer bias, chargeback representment variance, and missing documents.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from backend.config import DATA_DIR

RNG = np.random.default_rng(42)

REASON_CODES = [
    "item_not_received",         # Visa 13.1 / MC 4855
    "item_not_as_described",     # Visa 13.3 / MC 4853
    "duplicate_charge",          # Visa 12.6 / MC 4834
    "unrecognized_transaction",   # Visa 10.4 / MC 4837 (Fraud)
    "subscription_cancelled",    # Visa 13.7 / MC 4841
]

MERCHANTS = ["MERCH_RETAIL_01", "MERCH_SAAS_02", "MERCH_ECOM_03", "MERCH_DIGITAL_04"]


def _generate_synthetic_records(n_samples: int = 5000) -> pd.DataFrame:
    records = []
    base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    for i in range(n_samples):
        reason = RNG.choice(REASON_CODES, p=[0.35, 0.15, 0.15, 0.25, 0.10])
        merchant_id = RNG.choice(MERCHANTS, p=[0.40, 0.25, 0.25, 0.10])
        
        # Temporal ordering over a 180-day window
        days_offset = RNG.integers(0, 180)
        txn_timestamp = base_date + timedelta(days=int(days_offset), hours=int(RNG.integers(0, 24)))
        days_since_txn = 180 - days_offset

        delivery_confirmed = RNG.random() < 0.62
        tracking_matches_address = delivery_confirmed and (RNG.random() < 0.85)
        signed_delivery_proof = delivery_confirmed and (RNG.random() < 0.50)
        
        device_matches_prior_orders = RNG.random() < 0.68
        ip_geo_matches_billing = RNG.random() < 0.72
        customer_prior_clean_orders = int(RNG.poisson(lam=3.5))
        support_ticket_exists = RNG.random() < 0.45
        
        # Amount follows heavy-tailed log-gamma distribution
        amount_inr = float(np.round(RNG.gamma(shape=2.2, scale=1200), 2))
        
        duplicate_txn_id_found = (reason == "duplicate_charge") and (RNG.random() < 0.75)
        subscription_cancel_logged = (reason == "subscription_cancelled") and (RNG.random() < 0.50)

        # Introduce Missingness (Imperfect merchant logs)
        if RNG.random() < 0.08:
            tracking_matches_address = False
        if RNG.random() < 0.05:
            ip_geo_matches_billing = False

        # Introduce Contradictory Evidence (e.g. proof signed but delivery not confirmed)
        is_contradictory = False
        if RNG.random() < 0.04:
            signed_delivery_proof = True
            delivery_confirmed = False
            is_contradictory = True

        # --- Latent Ground Truth Rule (With Unobserved Risk Noise) ---
        score = 0.0
        if reason == "item_not_received":
            score += 3.0 if signed_delivery_proof else (1.2 if delivery_confirmed else -2.5)
            score += 1.5 if tracking_matches_address else -0.5
        elif reason == "item_not_as_described":
            score += 1.8 if support_ticket_exists else -1.5
        elif reason == "duplicate_charge":
            score += 3.5 if duplicate_txn_id_found else -3.0
        elif reason == "unrecognized_transaction":
            score += 2.5 if (device_matches_prior_orders and ip_geo_matches_billing) else -2.5
            score += 1.2 if customer_prior_clean_orders >= 3 else -1.0
        elif reason == "subscription_cancelled":
            score += 3.2 if subscription_cancel_logged else -2.8

        score += 0.4 * min(customer_prior_clean_orders, 5)
        score -= 0.02 * days_since_txn

        # Add unobserved latent factor (e.g. issuer-specific leniency, merchant reputation)
        latent_unobserved_factor = RNG.normal(loc=0.0, scale=1.2)
        score += latent_unobserved_factor

        # Probability calculation with sigmoid
        p_win = 1.0 / (1.0 + np.exp(-(score - 0.3)))
        
        # Invert label with 8% probability (simulates human analyst / issuer error)
        win_prob = p_win if RNG.random() > 0.08 else (1.0 - p_win)
        outcome = "won" if RNG.random() < win_prob else "lost"

        records.append({
            "transaction_id": f"TXN{100000 + i}",
            "merchant_id": merchant_id,
            "created_at": txn_timestamp.isoformat(),
            "reason_code": reason,
            "amount_inr": amount_inr,
            "delivery_confirmed": delivery_confirmed,
            "tracking_matches_address": tracking_matches_address,
            "signed_delivery_proof": signed_delivery_proof,
            "device_matches_prior_orders": device_matches_prior_orders,
            "ip_geo_matches_billing": ip_geo_matches_billing,
            "customer_prior_clean_orders": customer_prior_clean_orders,
            "support_ticket_exists": support_ticket_exists,
            "duplicate_txn_id_found": duplicate_txn_id_found,
            "subscription_cancel_logged": subscription_cancel_logged,
            "days_since_transaction": days_since_txn,
            "is_contradictory": is_contradictory,
            "outcome": outcome,
        })

    return pd.DataFrame(records)


def generate_all_datasets():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    df = _generate_synthetic_records(n_samples=5000)
    
    # Save main disputes dataset
    df.to_csv(DATA_DIR / "disputes.csv", index=False)
    
    # Save relational supporting tables
    transactions = df[["transaction_id", "merchant_id", "created_at", "amount_inr"]]
    delivery = df[["transaction_id", "delivery_confirmed", "tracking_matches_address", "signed_delivery_proof"]]
    support = df[["transaction_id", "support_ticket_exists"]].copy()
    support["resolution"] = support["support_ticket_exists"].apply(
        lambda x: "customer_contacted_resolved" if x else "no_ticket_filed"
    )

    transactions.to_csv(DATA_DIR / "transactions.csv", index=False)
    delivery.to_csv(DATA_DIR / "delivery.csv", index=False)
    support.to_csv(DATA_DIR / "support_logs.csv", index=False)
    
    print(f"Generated {len(df)} synthetic dispute records.")
    print("Files updated in data/: disputes.csv, transactions.csv, delivery.csv, support_logs.csv")


if __name__ == "__main__":
    generate_all_datasets()