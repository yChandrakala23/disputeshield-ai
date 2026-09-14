# 🛡️ DisputeShield AI (Version 2.0)

## Production-Grade AI Chargeback Evidence & Risk Intelligence System

DisputeShield helps merchant payment operations teams evaluate chargeback defensibility, validate reason-code evidence completeness, draft grounded merchant representment letters using AI, and log operational actions to an append-only audit trail.

---

## 🚀 Key Production Upgrades (v2.0)

1. **Persistent Database Layer**: Built on SQLAlchemy ORM (`data/disputeshield.db`), persisting disputes, evidence snapshots, decisions, analyst override actions, and audit trails across server restarts.
2. **Startup Model Loading & Async Lifespan**: Loads calibrated ML models into memory ONCE at application startup, eliminating repeated disk reads and I/O bottlenecks.
3. **ML Benchmark & Calibration Suite**: Reproducible evaluation framework comparing 5 models (Majority Baseline, Heuristic Rules, Logistic Regression, RandomForest, Calibrated Gradient Boosting) on a 25% held-out test set with Brier calibration scores.
4. **Reason-Code Policy Engine**: Bounded decision matrix combining evidence completeness checks, contradiction safety overrides, and calibrated ML confidence thresholds.
5. **LLM Safety & Prompt Injection Defense**: Untrusted evidence text is wrapped in `<evidence_payload>` XML tags and sanitized against prompt injection keywords. Includes post-generation hallucination verification and safe deterministic fallback.
6. **Automated Adversarial Test Suite**: 12 automated unit, integration, and adversarial attack tests protecting against prompt injection, contradictory evidence, missing signals, and edge cases.

---

## 🏗️ Architecture

```
[Dispute Transaction] ──► [FastAPI Ingress (api.py)]
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
[SQLite DB / ORM]      [Policy Rules Engine]      [Calibrated ML Model]
(disputeshield.db)     (policy_engine.py)         (GradientBoosting)
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  ▼
                    [AsyncGroq LLM Service]
                    (Sanitized & Grounded)
                                  │
                                  ▼
                    [Human Analyst Review]
                    (Action & Override)
                                  │
                                  ▼
                    [Append-Only Audit Log]
```

---

## 🏃 Running & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Dataset & Train Models
```bash
python backend/data_gen.py
python backend/create_test_set.py
python backend/classifier.py
```

### 3. Run Automated Test Suite
```bash
pytest tests/
# or
python -m unittest discover tests
```

### 4. Start Backend API Server
```bash
uvicorn backend.api:app --reload --port 8000
```
- API Documentation available at: `http://localhost:8000/docs`

### 5. Start Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Security & Privacy Notice
- Operational write endpoints support optional `X-API-Key` header authentication.
- Audit logs automatically mask PII (email addresses, IP addresses) before writing to disk.
- All evaluation metrics are generated on a held-out test split.
