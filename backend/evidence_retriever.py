from pathlib import Path
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def retrieve_evidence(transaction_id: str) -> dict:
    """
    Fetch all available evidence for a disputed transaction.
    Simulates retrieval from merchant systems.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    delivery = pd.read_csv(DATA_DIR / "delivery.csv")
    support = pd.read_csv(DATA_DIR / "support_logs.csv")
    disputes = pd.read_csv(DATA_DIR / "disputes.csv")


    txn = transactions[
        transactions["transaction_id"] == transaction_id
    ]

    if txn.empty:
        return {}

    txn = txn.iloc[0]


    delivery_row = delivery[
        delivery["transaction_id"] == transaction_id
    ].iloc[0]


    support_row = support[
        support["transaction_id"] == transaction_id
    ].iloc[0]


    dispute_row = disputes[
        disputes["transaction_id"] == transaction_id
    ].iloc[0]


    return {
        "amount_inr": float(txn["amount_inr"]),

        "delivery_confirmed":
            bool(delivery_row["delivery_confirmed"]),

        "tracking_matches_address":
            bool(delivery_row["tracking_matches_address"]),

        "signed_delivery_proof":
            bool(delivery_row["signed_delivery_proof"]),

        "support_ticket_exists":
            bool(support_row["support_ticket_exists"]),

        "support_resolution":
            str(support_row["resolution"]),

        "duplicate_txn_id_found":
            bool(dispute_row["duplicate_txn_id_found"]),

        "reason_code":
            str(dispute_row["reason_code"]),

        "device_matches_prior_orders": bool(
    dispute_row["device_matches_prior_orders"]
),

        "ip_geo_matches_billing": bool(
    dispute_row["ip_geo_matches_billing"]
),

        "customer_prior_clean_orders": int(
    dispute_row["customer_prior_clean_orders"]
),

        "subscription_cancel_logged": bool(
    dispute_row["subscription_cancel_logged"]
),

        "days_since_transaction": int(
    dispute_row["days_since_transaction"]
),
    }
