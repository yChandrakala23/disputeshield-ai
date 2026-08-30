from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import joblib
import pandas as pd
from backend.evidence_retriever import retrieve_evidence
from backend.classifier import score_single
from backend.decision_engine import decide_action
from backend.evidence_drafter import draft_evidence_response
from backend.audit import log_decision, read_audit_log
from datetime import datetime, timedelta


app = FastAPI(
    title="DisputeShield AI",
    description="AI-powered chargeback dispute intelligence system",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
         "https://disputeshield-ai.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# IN-MEMORY CASE STATE
# Demo-friendly case management layer
# ============================================================

case_actions = {}


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "message": "DisputeShield AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# PROCESS DISPUTE
# ============================================================

@app.post("/disputes/{transaction_id}/process")
def process_dispute(transaction_id: str):

    # --------------------------------------------------------
    # 1. Retrieve evidence
    # --------------------------------------------------------

    evidence = retrieve_evidence(transaction_id)

    if not evidence:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    # --------------------------------------------------------
    # 2. Load ML model
    # --------------------------------------------------------

    model_bundle = joblib.load(
        "data/model.joblib"
    )


    # --------------------------------------------------------
    # 3. Prepare model input
    # --------------------------------------------------------

    row = pd.Series({

        "amount_inr":
            float(evidence["amount_inr"]),

        "delivery_confirmed":
            evidence["delivery_confirmed"],

        "tracking_matches_address":
            evidence["tracking_matches_address"],

        "signed_delivery_proof":
            evidence["signed_delivery_proof"],

        "device_matches_prior_orders":
            evidence["device_matches_prior_orders"],

        "ip_geo_matches_billing":
            evidence["ip_geo_matches_billing"],

        "customer_prior_clean_orders":
            evidence["customer_prior_clean_orders"],

        "support_ticket_exists":
            evidence["support_ticket_exists"],

        "duplicate_txn_id_found":
            evidence["duplicate_txn_id_found"],

        "subscription_cancel_logged":
            evidence["subscription_cancel_logged"],

        "days_since_transaction":
            evidence["days_since_transaction"],

        "reason_code":
            evidence["reason_code"]
    })


    # --------------------------------------------------------
    # 4. ML Prediction
    # --------------------------------------------------------

    label, confidence = score_single(
        model_bundle,
        row
    )


    # --------------------------------------------------------
    # 5. Decision Engine
    # --------------------------------------------------------

    decision = decide_action(
        confidence
    )


    # --------------------------------------------------------
    # 6. Generate AI Evidence Draft
    # --------------------------------------------------------

    draft = None

    if decision["action"] == "RECOMMEND_CONTEST":

        draft = draft_evidence_response(

            transaction_id,

            evidence["reason_code"],

            evidence,

            confidence
        )


    # --------------------------------------------------------
    # 7. Case Management Information
    # --------------------------------------------------------

    existing_action = case_actions.get(
        transaction_id
    )

    status = (
        existing_action["status"]
        if existing_action
        else "ANALYZED"
    )

    human_action = (
        existing_action["action"]
        if existing_action
        else None
    )


    # --------------------------------------------------------
    # 8. Audit Logging
    # --------------------------------------------------------

    audit_entry = log_decision(

        transaction_id,

        evidence["reason_code"],

        evidence,

        label,

        confidence,

        decision["action"],

        draft
    )


    # --------------------------------------------------------
    # 9. Return Result
    # --------------------------------------------------------

    response_deadline = (
       datetime.now() + timedelta(days=15)
).strftime("%Y-%m-%d")


    return {

    "transaction_id":
        transaction_id,

    "evidence":
        evidence,

    "prediction":
        label,

    "confidence":
        confidence,

    "decision":
        decision,

    "draft_response":
        draft,

    "case_status":
        status,

    "human_action":
        human_action,

    "response_deadline":
        response_deadline,

    "audit":
        audit_entry
}


# ============================================================
# CASE ACTION
# ============================================================

@app.post("/disputes/{transaction_id}/action")
def update_dispute_action(
    transaction_id: str,
    action: str
):

    allowed_actions = [
        "CONTEST",
        "ACCEPT"
    ]

    if action not in allowed_actions:

        raise HTTPException(
            status_code=400,
            detail="Invalid action"
        )


    status = (
        "CONTESTED"
        if action == "CONTEST"
        else "ACCEPTED"
    )


    case_actions[transaction_id] = {

        "action": action,

        "status": status,

        "timestamp":
            datetime.now().isoformat()
    }


    return {

        "transaction_id":
            transaction_id,

        "action":
            action,

        "status":
            status,

        "timestamp":
            case_actions[transaction_id]["timestamp"]
    }


# ============================================================
# AUDIT
# ============================================================

@app.get("/audit")
def get_audit():

    return read_audit_log()


# ============================================================
# METRICS
# ============================================================

@app.get("/metrics")
def get_metrics():

    return {

        "precision": 0.862,

        "recall": 0.869,

        "roc_auc": 0.905,

        "held_out_cases": 1250,

        "false_positive_cost": 56100,

        "modeled_recovered_value": 1006000,

        "net_modeled_value": 949900
    }
  