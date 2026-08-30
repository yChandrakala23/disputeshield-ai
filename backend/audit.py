"""
Audit trail: every decision the pipeline makes is logged with the
evidence it saw, the score behind it, and the outcome — flag / clear /
escalate-to-human. Nothing is decided silently.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "audit_log.jsonl"


def log_decision(
    transaction_id: str,
    reason_code: str,
    evidence: dict,
    label: str,
    confidence: float,
    action: str,
    draft_response: str | None = None,
) -> dict:
    """action: 'AUTO_CONTEST' | 'REVIEW_NOT_WORTH_CONTESTING' | 'HUMAN_REVIEW'"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transaction_id": transaction_id,
        "reason_code": reason_code,
        "evidence": evidence,
        "defensibility_label": label,
        "confidence": confidence,
        "action": action,
        "draft_response": draft_response,
    }
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_audit_log(limit: int = 100) -> list[dict]:
    if not AUDIT_LOG_PATH.exists():
        return []
    lines = AUDIT_LOG_PATH.read_text().strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]]