"""
DisputeShield API — chargeback evidence responder.

Endpoints:
  GET  /health
  GET  /metrics                    -> held-out precision/recall/AUC/FP-cost report
  GET  /disputes/sample?n=5        -> sample disputed transactions from the dataset
  POST /disputes/{transaction_id}/process  -> run the full pipeline on one dispute
  GET  /audit-log?limit=50         -> recent audit trail entries

Decision policy:
  confidence >= 0.65 -> auto_contest  (draft + submit evidence)
  confidence <= 0.35 -> auto_concede  (not worth contesting, log why)
  otherwise          -> escalate_human (ambiguous, sent to a human reviewer)
"""
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .audit import log_decision, read_audit_log
from .classifier import EvalResult, score_single, train_and_evaluate
from .evidence_drafter import draft_evidence_response

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_CSV = DATA_DIR / "disputes.csv"
MODEL_PATH = DATA_DIR / "model.joblib"

app = FastAPI(title="DisputeShield API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_df = pd.read_csv(DATA_CSV)
if not MODEL_PATH.exists():
    train_and_evaluate(_df, str(MODEL_PATH))
_model_bundle = joblib.load(MODEL_PATH)
_eval_result: EvalResult = train_and_evaluate(_df, str(MODEL_PATH))

EVIDENCE_FIELDS = [
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return {
        "precision": _eval_result.precision,
        "recall": _eval_result.recall,
        "roc_auc": _eval_result.roc_auc,
        "confusion_matrix": _eval_result.confusion,
        "false_positive_cost_inr": _eval_result.total_false_positive_cost_inr,
        "recovered_value_inr": _eval_result.total_recovered_value_inr,
        "net_value_inr": _eval_result.net_value_inr,
        "n_test_transactions": _eval_result.n_test,
        "note": "Metrics computed on a held-out 25% split, not the training set. "
        "FP-cost and recovered-value figures use stated illustrative cost "
        "assumptions (see classifier.py) pending real historical cost data.",
    }


@app.get("/disputes/sample")
def sample_disputes(n: int = 5):
    sample = _df.sample(n=min(n, len(_df)), random_state=None)
    return sample.to_dict(orient="records")


@app.post("/disputes/{transaction_id}/process")
def process_dispute(transaction_id: str):
    match = _df[_df["transaction_id"] == transaction_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="transaction_id not found in dataset")
    row = match.iloc[0]

    label, confidence = score_single(_model_bundle, row[EVIDENCE_FIELDS + ["reason_code"]])

    def _native(v):
        if isinstance(v, (bool, pd.BooleanDtype)):
            return bool(v)
        if hasattr(v, "item"):
            return v.item()
        return v

    evidence = {k: _native(row[k]) for k in EVIDENCE_FIELDS}

    if confidence >= 0.65:
        action = "auto_contest"
        draft = draft_evidence_response(transaction_id, row["reason_code"], evidence, confidence)
    elif confidence <= 0.35:
        action = "auto_concede"
        draft = None
    else:
        action = "escalate_human"
        draft = None

    entry = log_decision(
        transaction_id=transaction_id,
        reason_code=row["reason_code"],
        evidence=evidence,
        label=label,
        confidence=confidence,
        action=action,
        draft_response=draft,
    )
    return entry


@app.get("/audit-log")
def audit_log(limit: int = 50):
    return read_audit_log(limit=limit)
