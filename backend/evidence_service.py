"""
Evidence Retrieval & Assessment Service

Fetches evidence signals from transactions, delivery, support, and dispute records.
Evaluates evidence availability, completeness scores, and detects conflicting signals.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd

from backend.config import DATA_DIR
from backend.models import DisputeRecord


def retrieve_evidence_payload(transaction_id: str, db_session=None) -> Dict[str, Any]:
    """
    Fetch evidence payload for a transaction ID.
    If database record exists, load from DB; otherwise fall back to CSV source tables.
    """
    # 1. Try DB lookup first
    if db_session:
        dispute_db = db_session.query(DisputeRecord).filter(DisputeRecord.transaction_id == transaction_id).first()
        if dispute_db and dispute_db.evidence:
            return dispute_db.evidence.get_payload()

    # 2. Fall back to CSV sources
    transactions_path = DATA_DIR / "transactions.csv"
    delivery_path = DATA_DIR / "delivery.csv"
    support_path = DATA_DIR / "support_logs.csv"
    disputes_path = DATA_DIR / "disputes.csv"

    if not disputes_path.exists():
        return {}

    disputes = pd.read_csv(disputes_path)
    match = disputes[disputes["transaction_id"] == transaction_id]
    
    if match.empty:
        return {}

    row = match.iloc[0]

    evidence = {
        "amount_inr": float(row["amount_inr"]),
        "delivery_confirmed": bool(row["delivery_confirmed"]),
        "tracking_matches_address": bool(row["tracking_matches_address"]),
        "signed_delivery_proof": bool(row["signed_delivery_proof"]),
        "device_matches_prior_orders": bool(row["device_matches_prior_orders"]),
        "ip_geo_matches_billing": bool(row["ip_geo_matches_billing"]),
        "customer_prior_clean_orders": int(row["customer_prior_clean_orders"]),
        "support_ticket_exists": bool(row["support_ticket_exists"]),
        "duplicate_txn_id_found": bool(row.get("duplicate_txn_id_found", False)),
        "subscription_cancel_logged": bool(row.get("subscription_cancel_logged", False)),
        "days_since_transaction": int(row.get("days_since_transaction", 15)),
        "reason_code": str(row["reason_code"]),
        "is_contradictory": bool(row.get("is_contradictory", False)),
    }

    # Calculate Completeness Score (Ratio of positive/available evidence signals)
    boolean_signals = [
        "delivery_confirmed", "tracking_matches_address", "signed_delivery_proof",
        "device_matches_prior_orders", "ip_geo_matches_billing", "support_ticket_exists"
    ]
    present_signals = sum(1 for k in boolean_signals if evidence.get(k))
    evidence["completeness_score"] = round(present_signals / len(boolean_signals), 2)

    return evidence
