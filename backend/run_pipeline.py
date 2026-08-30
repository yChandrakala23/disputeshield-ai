import sys
import joblib
import pandas as pd

from evidence_retriever import retrieve_evidence
from classifier import score_single
from decision_engine import decide_action
from evidence_drafter import draft_evidence_response
from audit import log_decision


def run(transaction_id):

    print("\n==============================")
    print("      DISPUTESHIELD AI")
    print("==============================\n")


    # -------------------------
    # 1. Retrieve evidence
    # -------------------------

    evidence = retrieve_evidence(transaction_id)

    if not evidence:
        print("Transaction not found.")
        return

    print("===== EVIDENCE RETRIEVED =====")
    print(evidence)


    # -------------------------
    # 2. Load ML model
    # -------------------------

    model_bundle = joblib.load(
        "data/model.joblib"
    )


    # Convert retrieved evidence into model input

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


    # -------------------------
    # 3. ML prediction
    # -------------------------

    label, confidence = score_single(
        model_bundle,
        row
    )

    print("\n===== MODEL =====")
    print("Prediction:", label)
    print("Confidence:", confidence)


    # -------------------------
    # 4. Decision engine
    # -------------------------

    decision = decide_action(
        confidence
    )

    print("\n===== DECISION =====")
    print(decision)


    # -------------------------
    # 5. LLM Draft
    # -------------------------

    if decision["action"] == "RECOMMEND_CONTEST":

        draft = draft_evidence_response(

            transaction_id,

            evidence["reason_code"],

            evidence,

            confidence

        )

    else:

        draft = (
            "Draft not generated.\n"
            "Reason: Evidence strength "
            "does not support contest preparation."
        )


    print("\n===== RESPONSE DRAFT =====")
    print(draft)


    # -------------------------
    # 6. Audit Trail
    # -------------------------

    audit_entry = log_decision(

        transaction_id,

        evidence["reason_code"],

        evidence,

        label,

        confidence,

        decision["action"],

        draft

    )


    print("\n===== AUDIT LOGGED =====")
    print(audit_entry)


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage: python backend/run_pipeline.py TXN_ID"
        )

        exit()


    run(
        sys.argv[1]
    )