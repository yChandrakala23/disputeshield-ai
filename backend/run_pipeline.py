import sys
from backend.database import init_db, SessionLocal
from backend.evidence_service import retrieve_evidence_payload
from backend.ml_service import ml_service
from backend.policy_engine import evaluate_dispute_policy
from backend.evidence_drafter import draft_evidence_response
from backend.audit_service import record_audit_event


def run(transaction_id: str):
    print("\n==============================")
    print("      DISPUTESHIELD AI v2.0")
    print("==============================\n")

    init_db()
    ml_service.load_model()
    db = SessionLocal()

    try:
        evidence = retrieve_evidence_payload(transaction_id, db_session=db)
        if not evidence:
            print(f"Error: Transaction '{transaction_id}' not found.")
            return

        print("===== EVIDENCE RETRIEVED =====")
        print(evidence)

        prediction_label, confidence = ml_service.score_dispute(evidence)
        print("\n===== ML ASSESSMENT =====")
        print(f"Prediction: {prediction_label} | Confidence: {confidence:.2%}")

        policy_res = evaluate_dispute_policy(
            reason_code=evidence.get("reason_code", ""),
            evidence=evidence,
            confidence=confidence
        )

        print("\n===== POLICY ENGINE DECISION =====")
        print(f"Action: {policy_res['action']}")
        print(f"Reason: {policy_res['reason']}")
        print(f"Requires Human Review: {policy_res['requires_human_review']}")

        draft_response = None
        if policy_res["action"] == "RECOMMEND_CONTEST":
            draft_response, draft_status, meta = draft_evidence_response(
                transaction_id=transaction_id,
                reason_code=evidence.get("reason_code", ""),
                evidence=evidence,
                confidence=confidence
            )
            print("\n===== GENERATED EVIDENCE DRAFT =====")
            print(f"Draft Status: {draft_status}")
            print(draft_response)

        audit_entry = record_audit_event(
            transaction_id=transaction_id,
            event_type="CLI_DISPUTE_PROCESSED",
            payload={
                "evidence": evidence,
                "confidence": confidence,
                "decision": policy_res,
                "draft_status": draft_response if draft_response else "N/A"
            },
            db_session=db
        )
        print("\n===== AUDIT RECORDED =====")
        print(f"Audit Event Timestamp: {audit_entry['timestamp']}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/run_pipeline.py TXN100001")
        sys.exit(1)
    run(sys.argv[1])