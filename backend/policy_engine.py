"""
DisputeShield Policy Engine (Version 2.1 - Red-Team Hardened)

Evaluates dispute evidence completeness, contradiction flags, card network rule compliance,
and ML confidence scores to derive bounded business decisions.

Boundary Guardrails:
1. Invalid / Negative / Extreme Amounts (Amount <= 0 or Amount > INR 10,000,000) -> Route to HUMAN_REVIEW.
2. NaN / Inf float values -> Route to HUMAN_REVIEW.
3. Contradictory Evidence Flag -> Mandatory HUMAN_REVIEW safety override.
4. Reason-Code Evidence Completeness Check.
5. ML Confidence Thresholding.
"""

import math
from typing import Dict, Any
from backend.config import settings


def evaluate_dispute_policy(
    reason_code: str,
    evidence: Dict[str, Any],
    confidence: float,
    contest_threshold: float = None,
    concede_threshold: float = None
) -> Dict[str, Any]:
    contest_threshold = contest_threshold or settings.CONTEST_THRESHOLD
    concede_threshold = concede_threshold or settings.CONCEDE_THRESHOLD

    policy_checks = {
        "reason_code_supported": True,
        "evidence_complete": True,
        "missing_required_signals": [],
        "is_contradictory": evidence.get("is_contradictory", False) if isinstance(evidence, dict) else False,
        "rule_violations": []
    }

    # 1. Input Sanitization & Boundary Guardrails
    amount_inr = evidence.get("amount_inr", 0.0) if isinstance(evidence, dict) else 0.0
    
    # Check for NaN / Infinity
    if math.isnan(confidence) or math.isinf(confidence) or math.isnan(amount_inr) or math.isinf(amount_inr):
        policy_checks["rule_violations"].append("Invalid mathematical float value (NaN/Infinity) detected.")
        return {
            "action": "HUMAN_REVIEW",
            "reason": "Invalid numerical data (NaN/Infinity) detected in dispute payload. Mandatory human review required.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }

    # Check bounds on Amount
    if amount_inr <= 0:
        policy_checks["rule_violations"].append("Non-positive transaction amount.")
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"Invalid transaction amount (INR {amount_inr}). Zero or negative amounts cannot be auto-contested.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }

    if amount_inr > 10_000_000.0:  # INR 1 Crore
        policy_checks["rule_violations"].append("High-value transaction exceeding automated threshold (INR 1 Crore).")
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"High-value transaction (INR {amount_inr:,.2f}) exceeds automated limit. Escalated to Senior Risk Analyst.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }

    # 2. Contradiction Flag Override
    if policy_checks["is_contradictory"]:
        return {
            "action": "HUMAN_REVIEW",
            "reason": "Contradictory evidence detected (e.g. signed delivery proof present without confirmed delivery). Mandatory analyst review required.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }

    # 3. Reason-Code specific evidence checks
    clean_reason = str(reason_code or "").strip().lower()

    if clean_reason == "item_not_received":
        if not (evidence.get("delivery_confirmed") or evidence.get("signed_delivery_proof")):
            policy_checks["evidence_complete"] = False
            policy_checks["missing_required_signals"].append("proof_of_delivery")

    elif clean_reason == "duplicate_charge":
        if not evidence.get("duplicate_txn_id_found"):
            policy_checks["evidence_complete"] = False
            policy_checks["missing_required_signals"].append("duplicate_transaction_reference")

    elif clean_reason == "subscription_cancelled":
        if not evidence.get("subscription_cancel_logged"):
            policy_checks["evidence_complete"] = False
            policy_checks["missing_required_signals"].append("cancellation_timestamp_log")

    elif clean_reason == "unrecognized_transaction":
        if not (evidence.get("device_matches_prior_orders") or evidence.get("ip_geo_matches_billing")):
            policy_checks["evidence_complete"] = False
            policy_checks["missing_required_signals"].append("customer_identity_consistency")

    elif clean_reason == "item_not_as_described":
        if not evidence.get("support_ticket_exists"):
            policy_checks["evidence_complete"] = False
            policy_checks["missing_required_signals"].append("support_communication_log")
    else:
        policy_checks["reason_code_supported"] = False
        policy_checks["rule_violations"].append(f"Reason code '{reason_code}' unsupported by automated rules matrix.")

    # 4. Action Determination based on Policy & Score
    if not policy_checks["reason_code_supported"]:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"Dispute reason '{reason_code}' requires manual investigation by risk ops.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }

    if confidence >= contest_threshold:
        if policy_checks["evidence_complete"]:
            return {
                "action": "RECOMMEND_CONTEST",
                "reason": "High model confidence backed by complete supporting evidence signals.",
                "requires_human_review": False,
                "policy_checks": policy_checks
            }
        else:
            missing_str = ", ".join(policy_checks["missing_required_signals"])
            return {
                "action": "HUMAN_REVIEW",
                "reason": f"High ML score ({confidence:.0%}) but missing key evidence: [{missing_str}]. Analyst review recommended.",
                "requires_human_review": True,
                "policy_checks": policy_checks
            }

    elif confidence <= concede_threshold:
        return {
            "action": "RECOMMEND_NOT_CONTESTING",
            "reason": f"Low win probability ({confidence:.0%}). Evidence strength does not justify contest fees.",
            "requires_human_review": False,
            "policy_checks": policy_checks
        }

    else:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"Uncertain model confidence ({confidence:.0%}). Case routed for human review.",
            "requires_human_review": True,
            "policy_checks": policy_checks
        }
