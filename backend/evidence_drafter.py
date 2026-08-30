"""
Evidence drafter: for transactions the classifier scores as winnable,
generate a structured chargeback-evidence response using groq, grounded
strictly in the evidence fields that were actually retrieved. The prompt
explicitly forbids inventing facts not present in the evidence payload —
if a field is missing, the draft must say so rather than fabricate it.

Requires GROQ_API_KEY in the environment. If unset, falls back to
a deterministic template (still useful for demoing the pipeline shape
without needing a key).
"""
import os
from groq import Groq

EVIDENCE_SYSTEM_PROMPT = """
You are an AI dispute analyst assisting a payment operations team.

Generate a professional chargeback evidence response.

STRICT RULES:
- Use ONLY the evidence provided.
- Never invent facts.
- Never accuse the customer of fraud.
- Never create missing documents or information.
- Mention unavailable evidence as limitations.
- Keep tone neutral and professional.

Format:

## Dispute Summary

Brief overview of:
- Transaction ID
- Dispute reason
- Amount (if available)


## Supporting Evidence

Convert technical fields into human-readable points.

Use format:

✓ Evidence item


## Evidence Limitations

Mention missing information.

Use format:

× Missing evidence


## Merchant Response Draft

Write a professional request for dispute review.

Maximum 250 words.
"""

def _format_evidence(evidence: dict) -> str:

    readable = {
        "amount_inr": "Transaction amount",
        "duplicate_txn_id_found": "Duplicate transaction detected",
        "delivery_confirmed": "Delivery confirmed",
        "tracking_matches_address": "Tracking matches address",
        "signed_delivery_proof": "Signed delivery proof available",
        "support_ticket_exists": "Support ticket exists",
        "device_matches_prior_orders": "Device matches previous orders",
        "ip_geo_matches_billing": "IP location matches billing",
        "customer_prior_clean_orders": "Previous successful customer orders",
        "subscription_cancel_logged": "Subscription cancellation logged",
        "days_since_transaction": "Days since transaction",
        "reason_code": "Dispute reason"
    }


    lines = []

    for key, value in evidence.items():

        label = readable.get(key, key)

        lines.append(
            f"{label}: {value}"
        )

    return "\n".join(lines)


def draft_evidence_response(transaction_id: str, reason_code: str, evidence: dict, confidence: float) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    evidence_block = _format_evidence(evidence)

    if not api_key:
        # Deterministic fallback so the pipeline is demoable without a key.
        return (
            f"[TEMPLATE DRAFT — set ANTHROPIC_API_KEY for LLM-generated response]\n\n"
            f"Dispute: {transaction_id} — reason: {reason_code}\n\n"
            f"Evidence on file:\n{evidence_block}\n\n"
            f"Model confidence this dispute is winnable: {confidence:.0%}\n"
            f"Requested outcome: Uphold the original transaction based on the evidence above."
        )

    

    client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)
    user_prompt = (
        f"Transaction ID: {transaction_id}\n"
        f"Dispute reason: {reason_code}\n"
        f"Model confidence this dispute is winnable: {confidence:.0%}\n\n"
        f"Evidence retrieved:\n{evidence_block}\n\n"
        "Draft the chargeback evidence response."
    )
    response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": EVIDENCE_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ],
    max_tokens=500
)

    return response.choices[0].message.content