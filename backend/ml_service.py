"""
ML Service Handler

Manages loading the trained ML model bundle into application state at startup
and performing prediction inference.
"""

from typing import Tuple, Dict, Any
import joblib
import pandas as pd

from backend.config import settings
from backend.classifier import score_single_dispute, train_and_benchmark


class MLService:
    def __init__(self):
        self.model_bundle: Dict[str, Any] = {}
        self.is_loaded: bool = False

    def load_model(self):
        if not settings.MODEL_PATH.exists():
            print("Model artifact missing. Running benchmark suite to train initial model...")
            train_and_benchmark()
            
        self.model_bundle = joblib.load(settings.MODEL_PATH)
        self.is_loaded = True
        print(f"ML Model loaded successfully: {self.model_bundle.get('version', 'rf_v1.0')}")

    def score_dispute(self, evidence: Dict[str, Any]) -> Tuple[str, float]:
        if not self.is_loaded:
            self.load_model()
            
        row = pd.Series({
            "amount_inr": float(evidence.get("amount_inr", 0.0)),
            "delivery_confirmed": evidence.get("delivery_confirmed", False),
            "tracking_matches_address": evidence.get("tracking_matches_address", False),
            "signed_delivery_proof": evidence.get("signed_delivery_proof", False),
            "device_matches_prior_orders": evidence.get("device_matches_prior_orders", False),
            "ip_geo_matches_billing": evidence.get("ip_geo_matches_billing", False),
            "customer_prior_clean_orders": int(evidence.get("customer_prior_clean_orders", 0)),
            "support_ticket_exists": evidence.get("support_ticket_exists", False),
            "duplicate_txn_id_found": evidence.get("duplicate_txn_id_found", False),
            "subscription_cancel_logged": evidence.get("subscription_cancel_logged", False),
            "days_since_transaction": int(evidence.get("days_since_transaction", 15)),
            "reason_code": str(evidence.get("reason_code", "unrecognized_transaction")),
        })

        return score_single_dispute(self.model_bundle, row)


ml_service = MLService()
