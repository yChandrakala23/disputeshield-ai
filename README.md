# DisputeShield — AI Chargeback Evidence Responder

Razorpay Buildathon · AI Risk Manager track

Reads a disputed transaction, scores whether it's defensible against a
held-out-validated classifier, and — for winnable disputes — drafts a
grounded chargeback evidence response. Every decision is logged to an
audit trail with the evidence and confidence behind it.

## What's here

```
backend/
  data_gen.py        synthetic dispute dataset generator (documented ground-truth rule)
  classifier.py       defensibility classifier + held-out precision/recall/AUC/FP-cost report
  evidence_drafter.py  Claude-grounded evidence response drafter (template fallback w/o API key)
  audit.py             append-only audit log (JSONL)
  main.py               FastAPI app wiring it together
frontend/
  index.html            audit console — metrics + live decision log
data/                    generated dataset, trained model, audit log (created on first run)
```

## Run it

```bash
pip install -r requirements.txt

# optional — enables real LLM-drafted evidence responses instead of the template fallback
export ANTHROPIC_API_KEY=sk-...

# generate data + train the model (also happens automatically on first API startup)
python3 backend/data_gen.py
python3 backend/classifier.py

# start the API
uvicorn backend.main:app --reload --port 8000
```

Then open `frontend/index.html` in a browser (or serve it) — it talks to
`http://localhost:8000` by default.

## What to check first

- `GET /metrics` — precision/recall/ROC-AUC on a held-out 25% split, plus
  a modeled false-positive cost and net value. Not one cherry-picked win.
- `POST /disputes/{transaction_id}/process` — run the full pipeline on
  one dispute; try `TXN100012` or any ID from `GET /disputes/sample`.
- `data/audit_log.jsonl` — every decision, append-only, human-readable.

## Honesty notes (say this out loud in the pitch, don't hide it)

- The dataset is **synthetic**, generated from a documented rule (see
  `data_gen.py`) standing in for real historical dispute outcomes. Swap
  in real labeled data from Razorpay's test-mode APIs before trusting
  the numbers beyond a demo.
- The false-positive cost (₹550/case) and recovered-value multiplier are
  **stated illustrative assumptions**, not measured figures — flagged
  explicitly in the `/metrics` response so nobody mistakes them for real
  numbers.
- The evidence drafter is instructed to cite only retrieved evidence and
  say so when a field is missing, rather than invent details — this is
  enforced by the system prompt, not (yet) by an automated check. A real
  version would add a post-hoc grounding verifier.

## Next steps if you have more time

1. Swap synthetic data for real Razorpay test-mode transaction + dispute data.
2. Add a grounding-verification pass on the drafted evidence (does every
   claim in the draft trace to a retrieved field?).
3. Expand the decision policy (currently a fixed 0.35/0.65 confidence
   threshold) into something cost-sensitive using the FP-cost model.
4. Wire the frontend "process" button to a live dispute feed instead of
   the static sample dataset.
