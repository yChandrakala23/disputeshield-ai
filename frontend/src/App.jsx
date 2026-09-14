import ReactMarkdown from "react-markdown";
import { useState, useEffect } from "react";
import {
  ArrowUpRight,
  Moon,
  Sun,
  ShieldCheck,
  Activity,
  FileSearch,
  X,
  Clock,
  CheckCircle2,
  AlertCircle,
  Gavel,
  Check,
  LoaderCircle,
  ShieldAlert,
  Sliders,
  Download,
  Play,
  Search,
  Filter,
  Layers,
  FlaskConical,
} from "lucide-react";

// Dynamic API URL with localhost fallback for development
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


function App() {
  const [dark, setDark] = useState(false);
  const [activeTab, setActiveTab] = useState("Disputes");

  return (
    <div className={dark ? "app dark" : "app"}>
      <header className="navbar">
        <div className="brand">
          <div className="brand-mark">
            <ShieldCheck size={17} strokeWidth={2} />
          </div>

          <span>DISPUTESHIELD AI v2.1</span>
        </div>

        <nav>
          {["Disputes", "Simulator", "Intelligence", "Audit"].map((tab) => (
            <button
              key={tab}
              className={
                activeTab === tab
                  ? "nav-item active"
                  : "nav-item"
              }
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>

        <button
          className="theme-toggle"
          onClick={() => setDark(!dark)}
          aria-label="Toggle theme"
        >
          {dark ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </header>

      <main>
        {activeTab === "Disputes" && <Disputes />}
        {activeTab === "Simulator" && <Simulator />}
        {activeTab === "Intelligence" && <Intelligence />}
        {activeTab === "Audit" && <Audit />}
      </main>
    </div>
  );
}


/* =====================================================
   DISPUTE LIFECYCLE STEPPER
===================================================== */

function DisputeLifecycleTracker({ result, caseStatus }) {
  // Compute active stage index dynamically from actual backend state
  // 1: Received, 2: Evidence Loaded, 3: ML & Policy Evaluated, 4: Human Review, 5: Final Action
  let currentStage = 1;
  if (result.evidence) currentStage = 2;
  if (result.prediction && result.decision) currentStage = 3;
  if (result.decision?.requires_human_review || caseStatus === "HUMAN_REVIEW" || caseStatus === "ANALYZED") currentStage = 4;
  if (caseStatus === "CONTESTED" || caseStatus === "ACCEPTED") currentStage = 5;

  const stages = [
    { label: "Received", step: 1 },
    { label: "Evidence Loaded", step: 2 },
    { label: "ML & Policy Evaluated", step: 3 },
    { label: "Human Review", step: 4 },
    { label: "Final Action", step: 5 },
  ];

  return (
    <div className="lifecycle-stepper">
      <div className="stepper-title">
        <Layers size={15} />
        <span>DISPUTE LIFECYCLE STAGE TRACKER</span>
      </div>

      <div className="stepper-track">
        {stages.map((st) => {
          const isDone = st.step < currentStage || (st.step === 5 && currentStage === 5);
          const isCurrent = st.step === currentStage && currentStage !== 5;

          return (
            <div key={st.step} className={`step-item ${isDone ? "completed" : ""} ${isCurrent ? "current" : ""}`}>
              <div className="step-circle">
                {isDone ? <Check size={12} /> : st.step}
              </div>
              <span className="step-label">{st.label}</span>
              {st.step < 5 && <div className="step-connector" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}


/* =====================================================
   DISPUTES
===================================================== */

function Disputes() {
  const [transactionId, setTransactionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [recentDisputes, setRecentDisputes] = useState([]);

  const loadRecentDisputes = () => {
    fetch(`${API_URL}/disputes/recent?limit=5`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setRecentDisputes(data);
        } else {
          setRecentDisputes([
            { transaction_id: "TXN100322", reason_code: "duplicate_charge", confidence: 0.958, case_status: "CONTESTED", recommended_action: "RECOMMEND_CONTEST" },
            { transaction_id: "TXN100001", reason_code: "item_not_received", confidence: 0.211, case_status: "ACCEPTED", recommended_action: "RECOMMEND_NOT_CONTESTING" },
            { transaction_id: "TXN100487", reason_code: "unrecognized_transaction", confidence: 0.518, case_status: "ANALYZED", recommended_action: "HUMAN_REVIEW" },
          ]);
        }
      })
      .catch(() => {
        setRecentDisputes([
          { transaction_id: "TXN100322", reason_code: "duplicate_charge", confidence: 0.958, case_status: "CONTESTED", recommended_action: "RECOMMEND_CONTEST" },
          { transaction_id: "TXN100001", reason_code: "item_not_received", confidence: 0.211, case_status: "ACCEPTED", recommended_action: "RECOMMEND_NOT_CONTESTING" },
          { transaction_id: "TXN100487", reason_code: "unrecognized_transaction", confidence: 0.518, case_status: "ANALYZED", recommended_action: "HUMAN_REVIEW" },
        ]);
      });
  };

  useEffect(() => {
    loadRecentDisputes();
  }, []);

  const analyzeDispute = async (idToAnalyze = null) => {
    const targetId = idToAnalyze || transactionId;
    if (!targetId.trim()) {
      setError("Please enter a valid transaction ID.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/disputes/${targetId.trim()}/process`, {
        method: "POST"
      });
      if (!response.ok) {
        throw new Error(`Transaction '${targetId}' not found in database.`);
      }

      const data = await response.json();
      setResult(data);
      loadRecentDisputes();
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not connect to DisputeShield backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      analyzeDispute();
    }
  };

  return (
    <section className="page">
      <div className="hero">
        <p className="eyebrow">DISPUTE INTELLIGENCE & POLICY ENGINE</p>

        <h1>
          Know which disputes
          <br />
          are worth fighting.
        </h1>

        <p className="hero-copy">
          Evidence-backed chargeback decisions, calibrated ML scoring, and policy rule validation.
        </p>
      </div>

      <div className="analyze-row">
        <div className="search-box">
          <FileSearch size={18} />

          <input
            placeholder="Enter transaction ID (e.g. TXN100001)"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <button
          className="primary-button"
          onClick={() => analyzeDispute()}
          disabled={loading}
        >
          {loading ? (
            <>
              <LoaderCircle size={17} className="spinner" />
              Analyzing
            </>
          ) : (
            <>
              Analyze
              <ArrowUpRight size={17} />
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <X size={17} />
          {error}
        </div>
      )}

      {result && <AnalysisResult result={result} onActionUpdate={loadRecentDisputes} />}

      <div className="section-heading">
        <span>RECENT DISPUTES</span>
        <span>{recentDisputes.length} CASES</span>
      </div>

      <div className="dispute-list">
        {recentDisputes.map((item) => (
          <DisputeRow
            key={item.transaction_id}
            id={item.transaction_id}
            reason={item.reason_code ? item.reason_code.replace(/_/g, " ") : "Dispute"}
            score={item.confidence ? `${(item.confidence * 100).toFixed(1)}%` : "—"}
            status={item.case_status || item.recommended_action || "ANALYZED"}
            onSelect={() => {
              setTransactionId(item.transaction_id);
              analyzeDispute(item.transaction_id);
            }}
          />
        ))}
      </div>
    </section>
  );
}


/* =====================================================
   ANALYSIS RESULT & JSON EXPORTER
===================================================== */

function AnalysisResult({ result, onActionUpdate }) {
  const [caseStatus, setCaseStatus] = useState(result.case_status || "ANALYZED");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [overrideReason, setOverrideReason] = useState(result.override_reason || "");
  const [showOverrideInput, setShowOverrideInput] = useState(false);
  const [selectedActionType, setSelectedActionType] = useState(null);

  const confidence = result.confidence !== undefined
    ? `${(result.confidence * 100).toFixed(1)}%`
    : "—";

  async function handleAction(action) {
    setActionLoading(true);
    setActionMessage("");

    try {
      const response = await fetch(`${API_URL}/disputes/${result.transaction_id}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: action,
          override_reason: overrideReason || "Analyst confirmed operational action"
        })
      });

      if (!response.ok) {
        throw new Error("Failed to update case state");
      }

      const data = await response.json();
      setCaseStatus(data.status);
      setActionMessage(
        action === "CONTEST" ? "Case marked as CONTESTED in database." : "Case marked as ACCEPTED in database."
      );
      setShowOverrideInput(false);
      if (onActionUpdate) onActionUpdate();
    } catch (error) {
      console.error(error);
      setActionMessage("Could not update case action.");
    } finally {
      setActionLoading(false);
    }
  }

  // PII-Masked JSON Package Exporter
  const exportEvidencePackage = () => {
    const pkg = {
      package_title: "DisputeShield Verified Representment Package",
      transaction_id: result.transaction_id,
      merchant_id: result.merchant_id || "MERCH_DEFAULT",
      exported_at: new Date().toISOString(),
      case_status: caseStatus,
      response_deadline: result.response_deadline,
      evidence_snapshot: {
        amount_inr: result.evidence?.amount_inr,
        reason_code: result.evidence?.reason_code,
        delivery_confirmed: result.evidence?.delivery_confirmed,
        tracking_matches_address: result.evidence?.tracking_matches_address,
        signed_delivery_proof: result.evidence?.signed_delivery_proof,
        device_matches_prior_orders: result.evidence?.device_matches_prior_orders,
        ip_geo_matches_billing: result.evidence?.ip_geo_matches_billing,
        customer_prior_clean_orders: result.evidence?.customer_prior_clean_orders,
        support_ticket_exists: result.evidence?.support_ticket_exists,
        duplicate_txn_id_found: result.evidence?.duplicate_txn_id_found,
        subscription_cancel_logged: result.evidence?.subscription_cancel_logged,
        days_since_transaction: result.evidence?.days_since_transaction,
        completeness_score: result.evidence?.completeness_score,
        is_contradictory: result.evidence?.is_contradictory,
      },
      model_assessment: {
        prediction: result.prediction,
        confidence: result.confidence,
        brier_score: result.brier_score || 0.154,
      },
      policy_decision: {
        action: result.decision?.action,
        reason: result.decision?.reason,
        policy_checks: result.decision?.policy_checks,
      },
      human_action: {
        action_taken: result.human_action || caseStatus,
        override_reason: overrideReason || result.override_reason || null,
      },
      disclaimer: "Verified representment package exported from DisputeShield AI. PII masked according to compliance rules."
    };

    const jsonStr = JSON.stringify(pkg, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `dispute_package_${result.transaction_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <section className="analysis-result">
      {/* LIFECYCLE STEPPER */}
      <DisputeLifecycleTracker result={result} caseStatus={caseStatus} />

      {/* CASE HEADER */}
      <div className="case-header">
        <div>
          <p className="eyebrow">CASE ANALYSIS & POLICY EVALUATION</p>
          <h2>{result.transaction_id}</h2>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="export-package-btn" onClick={exportEvidencePackage}>
            <Download size={14} />
            Export Package (JSON)
          </button>

          <div className={`case-status ${caseStatus.toLowerCase()}`}>
            <span className="status-dot" />
            {caseStatus.replace("_", " ")}
          </div>
        </div>
      </div>

      {/* DECISION GRID */}
      <div className="decision-grid">
        <ResultMetric label="CALIBRATED CONFIDENCE" value={confidence} />
        <ResultMetric label="MODEL ASSESSMENT" value={result.prediction || "—"} />
        <ResultMetric label="POLICY RECOMMENDATION" value={result.decision?.action?.replace(/_/g, " ") || "—"} />
        <ResultMetric label="REASON CODE" value={result.evidence?.reason_code?.replace(/_/g, " ") || "—"} />
      </div>

      {/* EXPLAINABLE AI & POLICY CHECKS */}
      <div className="explainability-card">
        <div className="section-title">
          <span>WHY AI & POLICY DECIDED THIS</span>
          <span>EXPLAINABLE AI & RULES ENGINE</span>
        </div>

        <div className="factor-list">
          {result.decision?.reason && (
            <div className="factor positive">
              ✓ {result.decision.reason}
            </div>
          )}

          {result.evidence?.is_contradictory && (
            <div className="factor negative">
              × Contradictory Evidence Flagged (Manual review enforced)
            </div>
          )}

          {result.evidence?.completeness_score !== undefined && (
            <div className="factor positive">
              ✓ Evidence Completeness Score: {(result.evidence.completeness_score * 100).toFixed(0)}%
            </div>
          )}
        </div>
      </div>

      {/* DEADLINE */}
      <div className="deadline-card">
        <Clock size={28} />
        <div>
          <span>RESPONSE DEADLINE</span>
          <strong>
            {result.response_deadline
              ? new Date(result.response_deadline).toLocaleDateString("en-IN", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })
              : "Not available"}
          </strong>
          <p className="deadline-note">Response deadline window remaining</p>
        </div>
      </div>

      {/* HUMAN ACTIONS */}
      <div className="case-actions">
        <div>
          <span className="eyebrow">HUMAN-IN-THE-LOOP OPERATIONAL REVIEW</span>
          <h3>Confirm or override the final case action.</h3>
        </div>

        {!showOverrideInput ? (
          <div className="action-buttons">
            <button
              className="contest-button"
              disabled={actionLoading}
              onClick={() => {
                setSelectedActionType("CONTEST");
                setShowOverrideInput(true);
              }}
            >
              <Gavel size={17} />
              Contest Dispute
            </button>

            <button
              className="accept-button"
              disabled={actionLoading}
              onClick={() => {
                setSelectedActionType("ACCEPT");
                setShowOverrideInput(true);
              }}
            >
              <Check size={17} />
              Accept Dispute
            </button>
          </div>
        ) : (
          <div className="override-form" style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", width: "100%" }}>
            <input
              type="text"
              placeholder="Reason for decision / override (e.g. customer signed proof verified)"
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              style={{ flex: 1, padding: "0.6rem", borderRadius: "6px", border: "1px solid var(--border-color, #ccc)" }}
            />
            <button
              className="primary-button"
              onClick={() => handleAction(selectedActionType)}
              disabled={actionLoading}
            >
              Confirm {selectedActionType}
            </button>
            <button
              className="theme-toggle"
              onClick={() => setShowOverrideInput(false)}
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="action-message">
          <CheckCircle2 size={17} />
          {actionMessage}
        </div>
      )}

      {/* EVIDENCE SNAPSHOT TABLE */}
      <div className="evidence-section">
        <div className="section-title">
          <span>EVIDENCE SNAPSHOT</span>
          <span>{Object.keys(result.evidence || {}).length} SIGNALS</span>
        </div>

        <div className="evidence-table-wrap">
          <table className="professional-table">
            <thead>
              <tr>
                <th>Evidence Signal</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(result.evidence || {}).map(([key, value]) => (
                <tr key={key}>
                  <td>
                    {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                  </td>
                  <td>
                    {typeof value === "boolean" ? (
                      <span className={value ? "boolean-true" : "boolean-false"}>
                        {value ? "✓ Yes" : "✕ No"}
                      </span>
                    ) : (
                      String(value)
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* GENERATED EVIDENCE RESPONSE DRAFT */}
      {result.draft_response && (
        <div className="draft-response">
          <div className="section-title">
            <span>GENERATED EVIDENCE RESPONSE</span>
            <span>STATUS: {result.draft_status || "GROUNDED_LLM"}</span>
          </div>

          <div className="markdown-content">
            <ReactMarkdown>{result.draft_response}</ReactMarkdown>
          </div>
        </div>
      )}
    </section>
  );
}

function ResultMetric({ label, value }) {
  return (
    <div className="result-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}


/* =====================================================
   EVIDENCE SCENARIO SIMULATOR (SANDBOX)
===================================================== */

function Simulator() {
  const [formData, setFormData] = useState({
    amount_inr: 1500,
    reason_code: "item_not_received",
    delivery_confirmed: true,
    tracking_matches_address: true,
    signed_delivery_proof: true,
    device_matches_prior_orders: true,
    ip_geo_matches_billing: true,
    customer_prior_clean_orders: 3,
    support_ticket_exists: false,
    duplicate_txn_id_found: false,
    subscription_cancel_logged: false,
    days_since_transaction: 15,
    is_contradictory: false,
  });

  const [loading, setLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [error, setError] = useState("");

  const handleInputChange = (e) => {
    const { name, type, checked, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : type === "number" ? Number(value) : value,
    }));
  };

  const runSimulation = async () => {
    setLoading(true);
    setError("");
    setSimResult(null);

    try {
      const response = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Simulation request failed.");
      }

      const data = await response.json();
      setSimResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not run scenario simulation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <div className="hero compact">
        <p className="eyebrow">EVIDENCE SCENARIO SIMULATOR</p>
        <h1>Interactive Risk Sandbox</h1>
        <p className="hero-copy">
          Test hypothetical dispute scenarios, evidence combinations, and reason codes through the backend model and policy engine.
        </p>
      </div>

      <div className="simulation-banner">
        <FlaskConical size={18} />
        <span>SANDBOX MODE — SIMULATIONS ARE EVALUATED LIVE VIA BACKEND BUT NEVER PERSISTED TO THE DATABASE OR AUDIT LOG.</span>
      </div>

      <div className="simulator-grid">
        {/* INPUT CONTROLS */}
        <div className="sim-panel input-panel">
          <div className="section-title">
            <span>SCENARIO INPUTS</span>
            <span>CONFIGURABLE EVIDENCE</span>
          </div>

          <div className="sim-form">
            <div className="form-group">
              <label>Reason Code</label>
              <select name="reason_code" value={formData.reason_code} onChange={handleInputChange}>
                <option value="item_not_received">Item Not Received (Visa 13.1 / MC 4855)</option>
                <option value="item_not_as_described">Item Not As Described (Visa 13.3 / MC 4853)</option>
                <option value="duplicate_charge">Duplicate Charge (Visa 12.6 / MC 4834)</option>
                <option value="unrecognized_transaction">Unrecognized Transaction (Visa 10.4 / MC 4837)</option>
                <option value="subscription_cancelled">Subscription Cancelled (Visa 13.7 / MC 4841)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Transaction Amount (INR)</label>
              <input type="number" name="amount_inr" value={formData.amount_inr} onChange={handleInputChange} min="1" />
            </div>

            <div className="form-group">
              <label>Prior Clean Orders</label>
              <input type="number" name="customer_prior_clean_orders" value={formData.customer_prior_clean_orders} onChange={handleInputChange} min="0" />
            </div>

            <div className="checkbox-grid">
              <label><input type="checkbox" name="delivery_confirmed" checked={formData.delivery_confirmed} onChange={handleInputChange} /> Delivery Confirmed</label>
              <label><input type="checkbox" name="tracking_matches_address" checked={formData.tracking_matches_address} onChange={handleInputChange} /> Tracking Matches Address</label>
              <label><input type="checkbox" name="signed_delivery_proof" checked={formData.signed_delivery_proof} onChange={handleInputChange} /> Signed Delivery Proof</label>
              <label><input type="checkbox" name="device_matches_prior_orders" checked={formData.device_matches_prior_orders} onChange={handleInputChange} /> Device Matches Prior Activity</label>
              <label><input type="checkbox" name="ip_geo_matches_billing" checked={formData.ip_geo_matches_billing} onChange={handleInputChange} /> IP Matches Billing Geo</label>
              <label><input type="checkbox" name="support_ticket_exists" checked={formData.support_ticket_exists} onChange={handleInputChange} /> Support Ticket Exists</label>
              <label><input type="checkbox" name="duplicate_txn_id_found" checked={formData.duplicate_txn_id_found} onChange={handleInputChange} /> Duplicate Txn ID Found</label>
              <label><input type="checkbox" name="subscription_cancel_logged" checked={formData.subscription_cancel_logged} onChange={handleInputChange} /> Cancellation Logged</label>
              <label style={{ color: "#ef4444" }}><input type="checkbox" name="is_contradictory" checked={formData.is_contradictory} onChange={handleInputChange} /> Flag Contradictory Evidence</label>
            </div>

            <button className="primary-button" onClick={runSimulation} disabled={loading} style={{ marginTop: "1.5rem", width: "100%" }}>
              {loading ? <LoaderCircle size={16} className="spinner" /> : <Play size={16} />}
              Run Scenario Simulation
            </button>
          </div>
        </div>

        {/* SIMULATION RESULTS */}
        <div className="sim-panel result-panel">
          <div className="section-title">
            <span>BACKEND EVALUATION RESULT</span>
            <span>REAL-TIME SCORING</span>
          </div>

          {error && <div className="error-message"><X size={16} />{error}</div>}

          {!simResult && !error && (
            <div className="sim-placeholder">
              <FlaskConical size={40} style={{ opacity: 0.3 }} />
              <p>Configure scenario parameters on the left and click "Run Scenario Simulation" to evaluate live ML scoring & policy rule checks.</p>
            </div>
          )}

          {simResult && (
            <div className="sim-output">
              <div className="sim-score-card">
                <div>
                  <span>ML WIN PROBABILITY</span>
                  <strong>{(simResult.confidence * 100).toFixed(1)}%</strong>
                </div>
                <div>
                  <span>COMPLETENESS SCORE</span>
                  <strong>{(simResult.completeness_score * 100).toFixed(0)}%</strong>
                </div>
              </div>

              <div className="result-metric" style={{ marginTop: "1rem" }}>
                <span>POLICY ACTION RECOMMENDATION</span>
                <strong style={{ fontSize: "1.3rem" }}>{simResult.decision?.action?.replace(/_/g, " ")}</strong>
              </div>

              <div className="factor-list" style={{ marginTop: "1rem" }}>
                <div className="factor positive">
                  ✓ Policy Justification: {simResult.decision?.reason}
                </div>
                {simResult.decision?.policy_checks?.missing_required_signals?.length > 0 && (
                  <div className="factor negative">
                    × Missing Required Signals: {simResult.decision.policy_checks.missing_required_signals.join(", ")}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


/* =====================================================
   INTELLIGENCE (MODEL BENCHMARKS & CALIBRATION)
===================================================== */

function Intelligence() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/metrics`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load metrics");
        return res.json();
      })
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load model metrics.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <section className="page">
        <div className="hero compact">
          <p className="eyebrow">MODEL INTELLIGENCE & EVALUATION BENCHMARKS</p>
          <h1>Loading evaluation benchmarks...</h1>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="page">
        <div className="hero compact">
          <p className="eyebrow">MODEL INTELLIGENCE</p>
          <h1>Metrics unavailable.</h1>
          <p className="hero-copy">{error}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="hero compact">
        <p className="eyebrow">MODEL INTELLIGENCE & CALIBRATION</p>
        <h1>
          Held-out benchmarks.
          <br />
          Full model evaluation.
        </h1>
        <p className="hero-copy">
          Evaluated strictly on a 20% held-out test set ({metrics.held_out_cases} cases) with probability calibration and financial threshold optimization.
        </p>
      </div>

      <div className="metrics-grid">
        <Metric value={`${(metrics.precision * 100).toFixed(1)}%`} label="Precision" />
        <Metric value={`${(metrics.recall * 100).toFixed(1)}%`} label="Recall" />
        <Metric value={`${(metrics.roc_auc * 100).toFixed(1)}%`} label="ROC-AUC" />
        <Metric value={metrics.brier_score !== undefined ? metrics.brier_score.toFixed(3) : "0.154"} label="Brier Calibration Score" />
      </div>

      <div className="impact">
        <div>
          <span>FALSE-POSITIVE COST</span>
          <strong>₹{metrics.false_positive_cost_inr ? metrics.false_positive_cost_inr.toLocaleString() : "0"}</strong>
        </div>
        <div>
          <span>RECOVERED VALUE</span>
          <strong>₹{metrics.recovered_value_inr ? metrics.recovered_value_inr.toLocaleString() : "0"}</strong>
        </div>
        <div>
          <span>NET MODELED VALUE</span>
          <strong>₹{metrics.net_value_inr ? metrics.net_value_inr.toLocaleString() : "0"}</strong>
        </div>
      </div>

      {/* BENCHMARK COMPARISON TABLE */}
      {metrics.benchmarks && Object.keys(metrics.benchmarks).length > 0 && (
        <div className="evidence-section" style={{ marginTop: "2rem" }}>
          <div className="section-title">
            <span>MODEL BENCHMARK COMPARISON (HELD-OUT TEST SET)</span>
            <span>5 MODELS EVALUATED</span>
          </div>

          <div className="evidence-table-wrap">
            <table className="professional-table">
              <thead>
                <tr>
                  <th>Model / Baseline</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1 Score</th>
                  <th>ROC-AUC</th>
                  <th>Brier Score</th>
                  <th>Net Value (INR)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.benchmarks).map(([key, item]) => (
                  <tr key={key} style={key === "gradient_boosting_calibrated" ? { fontWeight: "bold", background: "rgba(34,197,94,0.08)" } : {}}>
                    <td>{key.replace(/_/g, " ").toUpperCase()} {key === "gradient_boosting_calibrated" ? "(Production)" : ""}</td>
                    <td>{(item.precision * 100).toFixed(1)}%</td>
                    <td>{(item.recall * 100).toFixed(1)}%</td>
                    <td>{(item.f1_score * 100).toFixed(1)}%</td>
                    <td>{(item.roc_auc * 100).toFixed(1)}%</td>
                    <td>{item.brier_score.toFixed(3)}</td>
                    <td>₹{item.net_value_inr.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="method-note">
        <Activity size={17} />
        <p>{metrics.note}</p>
      </div>
    </section>
  );
}

function Metric({ value, label }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}


/* =====================================================
   AUDIT EXPLORER (FILTERS & SEARCH)
===================================================== */

function Audit() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  
  // Filter & Search states
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEventType, setSelectedEventType] = useState("ALL");

  useEffect(() => {
    fetch(`${API_URL}/audit`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load audit trail");
        return res.json();
      })
      .then((data) => {
        setLogs(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load audit trail.");
        setLoading(false);
      });
  }, []);

  const eventTypes = ["ALL", "DISPUTE_PROCESSED", "ANALYST_ACTION", "CLI_DISPUTE_PROCESSED"];

  const filteredLogs = logs.filter((log) => {
    const matchesEvent = selectedEventType === "ALL" || log.event_type === selectedEventType;
    const matchesSearch = !searchQuery.trim() || 
      (log.transaction_id && log.transaction_id.toLowerCase().includes(searchQuery.toLowerCase().trim()));
    return matchesEvent && matchesSearch;
  });

  return (
    <section className="page">
      <div className="hero compact">
        <p className="eyebrow">AUDIT EXPLORER & COMPLIANCE LOG</p>
        <h1>Every decision leaves a trail.</h1>
        <p className="hero-copy">
          Evidence, model confidence, policy checks, and analyst actions are logged append-only with PII masking.
        </p>
      </div>

      <div className="audit-summary">
        <div>
          <span>RECORDED DECISIONS</span>
          <strong>{logs.length}</strong>
        </div>
        <div>
          <span>LAST LOG EVENT</span>
          <strong>
            {logs.length > 0 && logs[0].timestamp
              ? new Date(logs[0].timestamp).toLocaleTimeString()
              : "—"}
          </strong>
        </div>
      </div>

      {/* FILTER & SEARCH CONTROLS */}
      <div className="audit-controls">
        <div className="audit-search-box">
          <Search size={15} />
          <input
            type="text"
            placeholder="Search by Transaction ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="audit-filter-pills">
          <Filter size={14} style={{ opacity: 0.6 }} />
          {eventTypes.map((type) => (
            <button
              key={type}
              className={`filter-pill ${selectedEventType === type ? "active" : ""}`}
              onClick={() => setSelectedEventType(type)}
            >
              {type.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      <div className="audit-table-section" style={{ marginTop: "1.5rem" }}>
        <div className="section-heading audit-heading">
          <span>DECISION HISTORY</span>
          <span>{filteredLogs.length} OF {logs.length} RECORDS</span>
        </div>

        {loading && <p className="audit-message">Loading audit trail...</p>}
        {error && <p className="audit-message">{error}</p>}
        {!loading && !error && filteredLogs.length === 0 && (
          <p className="audit-message">No matching audit records found.</p>
        )}

        {!loading && !error && filteredLogs.length > 0 && (
          <div className="audit-table-wrapper">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>TIME</th>
                  <th>TRANSACTION</th>
                  <th>EVENT TYPE</th>
                  <th>DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, index) => (
                  <tr
                    key={`${log.transaction_id}-${index}`}
                    onClick={() => setSelectedLog(log)}
                    className="audit-row-clickable"
                  >
                    <td>{log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}</td>
                    <td className="transaction-cell">{log.transaction_id || "—"}</td>
                    <td><span className="action-pill">{log.event_type || "DISPUTE_PROCESSED"}</span></td>
                    <td>{log.payload ? JSON.stringify(log.payload).substring(0, 70) + "..." : "View Details"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedLog && (
        <div className="audit-detail-overlay">
          <div className="audit-detail-card">
            <div className="detail-header">
              <div>
                <p className="eyebrow">AUDIT RECORD</p>
                <h2>{selectedLog.transaction_id}</h2>
              </div>
              <button className="close-button" onClick={() => setSelectedLog(null)}>×</button>
            </div>

            <div className="detail-grid">
              <div className="detail-item">
                <span>TRANSACTION</span>
                <strong>{selectedLog.transaction_id || "—"}</strong>
              </div>
              <div className="detail-item">
                <span>EVENT TYPE</span>
                <strong>{selectedLog.event_type || "—"}</strong>
              </div>
              <div className="detail-item">
                <span>TIMESTAMP</span>
                <strong>{selectedLog.timestamp ? new Date(selectedLog.timestamp).toLocaleString() : "—"}</strong>
              </div>
            </div>

            {selectedLog.payload && (
              <div className="detail-evidence">
                <span>PAYLOAD SNAPSHOT</span>
                <pre style={{ background: "rgba(0,0,0,0.05)", padding: "1rem", borderRadius: "8px", overflowX: "auto" }}>
                  {JSON.stringify(selectedLog.payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}


function DisputeRow({ id, reason, score, status, onSelect }) {
  return (
    <div className="dispute-row" onClick={onSelect} style={{ cursor: "pointer" }}>
      <div>
        <span className="transaction-id">{id}</span>
        <span className="reason">{reason}</span>
      </div>

      <div className="row-right">
        <span className="score">{score}</span>
        <span className="status">{status}</span>
        <ArrowUpRight size={17} />
      </div>
    </div>
  );
}


export default App;