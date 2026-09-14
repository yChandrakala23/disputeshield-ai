"""
DisputeShield Audit Service Layer

Provides append-only logging of dispute decisions, analyst overrides, and pipeline events.
Persists to database table (`audit_logs`) and secondary JSONL file (`data/audit_log.jsonl`).
Includes PII masking for sensitive fields.
"""

from datetime import datetime, timezone
import json
import re
from typing import Dict, Any, List

from backend.config import settings
from backend.models import AuditLogRecord


def _mask_pii(data: Any) -> Any:
    """Recursively mask PII strings such as email addresses, IP addresses, credit card numbers."""
    if isinstance(data, dict):
        return {k: _mask_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_mask_pii(item) for item in data]
    elif isinstance(data, str):
        # Mask IP address (e.g. 192.168.1.1 -> 192.168.x.x)
        data = re.sub(r'\b(\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}\b', r'\1.x.x', data)
        # Mask email (e.g. john.doe@example.com -> j***e@example.com)
        data = re.sub(r'\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b', r'\1***@\2', data)
        return data
    return data


def record_audit_event(
    transaction_id: str,
    event_type: str,
    payload: Dict[str, Any],
    db_session=None
) -> Dict[str, Any]:
    timestamp_str = datetime.now(timezone.utc).isoformat()
    masked_payload = _mask_pii(payload)

    entry = {
        "timestamp": timestamp_str,
        "transaction_id": transaction_id,
        "event_type": event_type,
        "payload": masked_payload
    }

    # 1. Log to DB if session provided
    if db_session:
        try:
            db_record = AuditLogRecord(
                transaction_id=transaction_id,
                event_type=event_type,
                payload_json=json.dumps(masked_payload)
            )
            db_session.add(db_record)
            db_session.commit()
        except Exception as e:
            print(f"Error persisting audit log to DB: {e}")
            db_session.rollback()

    # 2. Append to JSONL log file
    try:
        settings.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Error writing to audit_log.jsonl: {e}")

    return entry


def fetch_audit_logs(limit: int = 50, db_session=None) -> List[Dict[str, Any]]:
    # 1. Try DB first
    if db_session:
        try:
            records = db_session.query(AuditLogRecord).order_by(AuditLogRecord.id.desc()).limit(limit).all()
            if records:
                results = []
                for r in records:
                    results.append({
                        "id": r.id,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                        "transaction_id": r.transaction_id,
                        "event_type": r.event_type,
                        "payload": json.loads(r.payload_json) if r.payload_json else {}
                    })
                return results
        except Exception as e:
            print(f"Error reading audit log from DB: {e}")

    # 2. Fall back to JSONL file
    if not settings.AUDIT_LOG_PATH.exists():
        return []

    try:
        lines = settings.AUDIT_LOG_PATH.read_text().strip().splitlines()
        logs = [json.loads(line) for line in lines[-limit:]]
        logs.reverse()
        return logs
    except Exception as e:
        print(f"Error reading audit_log.jsonl: {e}")
        return []
