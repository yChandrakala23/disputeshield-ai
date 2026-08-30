# 🛡️ DisputeShield AI

## AI-powered chargeback dispute intelligence platform

**Razorpay Buildathon · AI Risk Manager track**

DisputeShield helps payment teams analyze chargeback disputes using machine learning, evidence retrieval, explainable AI, and human-in-the-loop decision workflows — reads a disputed transaction, scores whether it's defensible against a held-out-validated classifier, and drafts a grounded evidence response for winnable cases. Every decision is logged to an audit trail with the evidence and confidence behind it.

🔗 **Live demo:** [add your Vercel URL here]
📦 **API:** [add your Render URL here]

---

## 🚀 Problem

Chargeback disputes are expensive and time-consuming. Payment teams must manually review transaction evidence, determine dispute defensibility, prepare responses, and maintain audit records.

DisputeShield automates this workflow while keeping humans in control.

---

## ✨ Features

### 🤖 AI Dispute Assessment
- ML-based dispute defensibility prediction (RandomForest classifier)
- Confidence scoring
- Automated contest / accept / human-review recommendation

### 🔍 Evidence Intelligence
Retrieves and analyzes:
- Transaction information
- Delivery signals
- Support history
- Customer behavior patterns
- Payment consistency signals

### 🧠 Explainable AI
Provides:
- Decision factors, surfaced per transaction
- Supporting evidence, cited not invented
- Transparent reasoning behind every recommendation

### ✍️ AI-Assisted Response Drafting
Generates structured merchant chargeback responses using only retrieved evidence — grounded by system-prompt constraint, never fabricated.

### 👤 Human-in-the-Loop Review
Analysts can:
- Contest disputes
- Accept disputes
- Track case status

### 📋 Audit Trail
Records:
- Evidence retrieved
- Model confidence
- Decisions and their rationale
- Timestamps — append-only, nothing overwritten

### 📊 Model Intelligence Dashboard
Displays:
- Precision, recall, ROC-AUC — on a held-out split, not training data
- False-positive cost, modeled explicitly
- Net recovered value

---

## 🏗️ Architecture

```
   Transaction data (Razorpay test-mode / synthetic)
                    │
                    ▼
        ┌───────────────────────┐
        │  Defensibility model  │   RandomForest, trained on
        │    (classifier.py)    │   labeled dispute outcomes
        └───────────┬───────────┘
                     │ confidence score
                     ▼
        ┌───────────────────────┐
        │   Decision policy     │   ≥0.65 → contest
        │    (decision.py)      │   0.35–0.65 → human review
        └───────────┬───────────┘   ≤0.35 → not worth contesting
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  ┌───────────────┐   ┌──────────────────┐
  │ Evidence draft │   │   Audit log      │
  │ (Groq/Llama,   │   │   (audit.py)     │
  │ grounded only) │   │  append-only     │
  └───────────────┘   └──────────────────┘
          │                     │
          └──────────┬──────────┘
                      ▼
             FastAPI (main.py)
                      │
                      ▼
          Frontend dashboard (index.html)
```

**Tech stack:** FastAPI (Python) · scikit-learn (RandomForest) · Groq API for evidence drafting · pandas · React + Vite frontend · CSS · JSONL audit logging.

---

## 📁 What's here

```
backend/
  data_gen.py         synthetic dispute dataset generator (documented ground-truth rule)
  classifier.py        defensibility classifier + held-out precision/recall/AUC/FP-cost report
  decision.py           decision policy — confidence thresholds → action
  evidence_drafter.py   Groq-grounded evidence response drafter (template fallback w/o API key)
  audit.py               append-only audit log (JSONL)
  main.py                 FastAPI app wiring it together
frontend/
  index.html               dispute console — search, evidence detail, metrics, audit log
data/                       generated dataset, trained model, audit log (created on first run)
render.yaml                 Render deploy config
```

---

## 🏃 Run it locally

```bash
pip install -r requirements.txt

# optional — enables real LLM-drafted evidence responses instead of the template fallback
export GROQ_API_KEY=gsk_...   # free tier, no card required at console.groq.com

# generate data + train the model (also happens automatically on first API startup)
python3 backend/data_gen.py
python3 backend/classifier.py

# start the API
uvicorn backend.main:app --reload --port 8000
```

Then open `frontend/index.html` in a browser — it talks to `http://localhost:8000` by default (editable via the API URL field in the header for pointing at a deployed backend).

## What to check first

- `GET /metrics` — precision/recall/ROC-AUC on a held-out 25% split, plus a modeled false-positive cost and net value. Not one cherry-picked win.
- `POST /disputes/{transaction_id}/process` — run the full pipeline on one dispute; try `TXN100012` or any ID from `GET /disputes/sample`.
- `data/audit_log.jsonl` — every decision, append-only, human-readable.

---

## Honesty notes (said out loud in the pitch, not hidden)

- The dataset is **synthetic**, generated from a documented rule (see `data_gen.py`) standing in for real historical dispute outcomes. Swap in real labeled data from Razorpay's test-mode APIs before trusting the numbers beyond a demo.
- The false-positive cost (₹550/case) and recovered-value multiplier are **stated illustrative assumptions**, not measured figures — flagged explicitly in the `/metrics` response so nobody mistakes them for real numbers.
- The evidence drafter is instructed to cite only retrieved evidence and say so when a field is missing, rather than invent details — this is enforced by the system prompt, not yet by an automated check. A real version would add a post-hoc grounding verifier.

## Next steps if you have more time

1. Swap synthetic data for real Razorpay test-mode transaction + dispute data.
2. Add a grounding-verification pass on the drafted evidence (does every claim in the draft trace to a retrieved field?).
3. Make the decision policy's confidence thresholds cost-sensitive using the FP-cost model, instead of the current fixed 0.35 / 0.65 split.
4. Wire the dashboard to a live dispute feed instead of the static sample dataset.