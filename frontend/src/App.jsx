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
} from "lucide-react";

const API_URL = "https://disputeshield-api-xbt0.onrender.com";


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

          <span>DISPUTESHIELD</span>
        </div>

        <nav>
          {["Disputes", "Intelligence", "Audit"].map((tab) => (
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
        {activeTab === "Intelligence" && <Intelligence />}
        {activeTab === "Audit" && <Audit />}
      </main>
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

  const analyzeDispute = async () => {
    if (!transactionId.trim()) {
      setError("Please enter a transaction ID.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
  `${API_URL}/disputes/${transactionId}/process`,
  {
    method: "POST"
  }
);
      if (!response.ok) {
        throw new Error("Unable to process this transaction.");
      }

      const data = await response.json();

      console.log("API RESULT:", data);

      setResult(data);
    } catch (err) {
      console.error(err);

      setError(
        "Could not connect to the DisputeShield backend."
      );
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
        <p className="eyebrow">DISPUTE INTELLIGENCE</p>

        <h1>
          Know which disputes
          <br />
          are worth fighting.
        </h1>

        <p className="hero-copy">
          Evidence-backed chargeback decisions for modern payment operations.
        </p>
      </div>

      <div className="analyze-row">
        <div className="search-box">
          <FileSearch size={18} />

          <input
            placeholder="Enter transaction ID"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <button
          className="primary-button"
          onClick={analyzeDispute}
          disabled={loading}
        >
          {loading ? (
            <>
              <LoaderCircle
                size={17}
                className="spinner"
              />
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

      {result && <AnalysisResult result={result} />}

      <div className="section-heading">
        <span>RECENT DISPUTES</span>
        <span>3 CASES</span>
      </div>

      <div className="dispute-list">
        <DisputeRow
          id="TXN100322"
          reason="Duplicate charge"
          score="95.8%"
          status="CONTEST"
        />

        <DisputeRow
          id="TXN100001"
          reason="Item not received"
          score="21.1%"
          status="NOT CONTESTING"
        />

        <DisputeRow
          id="TXN100487"
          reason="Unrecognized transaction"
          score="51.8%"
          status="REVIEW"
        />
      </div>
    </section>
  );
}


/* =====================================================
   ANALYSIS RESULT
===================================================== */

function AnalysisResult({ result }) {

  const [caseStatus, setCaseStatus] = useState(
    result.case_status || "ANALYZED"
  );
  const updateCase = async(action)=>{

const response = await fetch(
`https://disputeshield-api-xbt0.onrender.com/disputes/${result.transaction_id}/action?action=${action}`,
{
method:"POST"
}
);


const data = await response.json();

setCaseStatus(data.status);

};

  const [actionLoading, setActionLoading] =
    useState(false);

  const [actionMessage, setActionMessage] =
    useState("");

  const confidence =
    result.confidence !== undefined
      ? `${(result.confidence * 100).toFixed(1)}%`
      : "—";


  // --------------------------------------------------
  // Deadline
  // --------------------------------------------------

  const deadline = result.deadline
    ? new Date(result.deadline)
    : null;

  const daysRemaining = deadline
    ? Math.max(
        0,
        Math.ceil(
          (deadline - new Date()) /
          (1000 * 60 * 60 * 24)
        )
      )
    : null;


  // --------------------------------------------------
  // Human action
  // --------------------------------------------------

  async function handleAction(action) {

    setActionLoading(true);
    setActionMessage("");

    try {

      const response = await fetch(
        `${API_URL}/disputes/${result.transaction_id}/action?action=${action}`,
        {
          method: "POST"
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update case");
      }

      const data = await response.json();

      setCaseStatus(data.status);

      setActionMessage(
        action === "CONTEST"
          ? "Case marked as contested."
          : "Case accepted."
      );

    } catch (error) {

      console.error(error);

      setActionMessage(
        "Could not update case."
      );

    } finally {

      setActionLoading(false);

    }
  }


  return (

    <section className="analysis-result">

      {/* ----------------------------------------- */}
      {/* CASE HEADER */}
      {/* ----------------------------------------- */}

      <div className="case-header">

        <div>

          <p className="eyebrow">
            CASE ANALYSIS COMPLETE
          </p>

          <h2>
            {result.transaction_id}
          </h2>

        </div>


        <div className={`case-status ${caseStatus.toLowerCase()}`}>

          <span className="status-dot" />

          {caseStatus.replace("_", " ")}



        </div>

      </div>


      {/* ----------------------------------------- */}
      {/* DECISION GRID */}
      {/* ----------------------------------------- */}

      <div className="decision-grid">

        <ResultMetric
          label="CONFIDENCE"
          value={confidence}
        />

        <ResultMetric
          label="MODEL ASSESSMENT"
          value={result.prediction || "—"}
        />

        <ResultMetric
          label="RECOMMENDED ACTION"
          value={
            result.decision?.action
              ?.replace(/_/g, " ")
              || "—"
          }
        />
        {/* Human review status */}

        <div className="explainability-card">

  <div className="section-title">
    <span>WHY AI DECIDED THIS</span>
    <span>EXPLAINABLE AI</span>
  </div>


  <div className="factor-list">

    {result.evidence?.duplicate_txn_id_found && (
      <div className="factor positive">
        ✓ Duplicate transaction detected
        <span>
          Strong supporting signal
        </span>
      </div>
    )}


    {result.evidence?.device_matches_prior_orders && (
      <div className="factor positive">
        ✓ Device matches previous customer activity
        <span>
          Customer consistency signal
        </span>
      </div>
    )}


    {result.evidence?.ip_geo_matches_billing && (
      <div className="factor positive">
        ✓ IP location matches billing information
        <span>
          Reduces fraud uncertainty
        </span>
      </div>
    )}


    {!result.evidence?.delivery_confirmed && (
      <div className="factor negative">
        × Delivery confirmation unavailable
        <span>
          Evidence limitation
        </span>
      </div>
    )}

  </div>

</div>
<div className="case-status">

   STATUS:

   <span>
      {caseStatus}
   </span>

</div>

<div className="review-badge">
  HUMAN REVIEW REQUIRED
</div>

        <ResultMetric
          label="REASON CODE"
          value={
            result.evidence?.reason_code
              ?.replace(/_/g, " ")
              || "—"
          }
        />

      </div>
      <div className="review-actions">

<button
className="contest-btn"
onClick={() => updateCase("CONTEST")}
>
✓ Contest Dispute
</button>


<button
className="accept-btn"
onClick={() => updateCase("ACCEPT")}
>
Accept Dispute
</button>

</div>


      {/* ----------------------------------------- */}
      {/* DEADLINE */}
      {/* ----------------------------------------- */}

      <div className="deadline-card">
  <Clock size={28} />

  <div>
    <span>RESPONSE DEADLINE</span>

    <strong>
      {result.response_deadline
        ? new Date(result.response_deadline).toLocaleDateString(
            "en-IN",
            {
              day: "2-digit",
              month: "short",
              year: "numeric",
            }
          )
        : "Not available"}
    </strong>

    {result.response_deadline && (
      <p className="deadline-note">
        Chargeback response window remaining
      </p>
    )}
  </div>
</div>

{/* ----------------------------------------- */}
{/* DISPUTE SUMMARY */}
{/* ----------------------------------------- */}

<div className="summary-card">

  <div className="section-title">
    <span>DISPUTE SUMMARY</span>
    <span>CASE OVERVIEW</span>
  </div>


  <p>
    The cardholder dispute for transaction{" "}
    <strong>
      {result.transaction_id}
    </strong>{" "}
    is classified under{" "}
    <strong>
      {result.evidence?.reason_code?.replace(/_/g," ")}
    </strong>.
  </p>


  <p>
    The AI assessment is based on retrieved transaction evidence,
    customer history, payment signals and available dispute context.
  </p>

</div>
      {/* ----------------------------------------- */}
      {/* AI RATIONALE */}
      {/* ----------------------------------------- */}

      <div className="rationale-card">

        <span>
          DECISION RATIONALE
        </span>

        <p>
          {result.decision?.reason ||
            "No decision rationale available."}
        </p>

      </div>


      {/* ----------------------------------------- */}
      {/* HUMAN ACTIONS */}
      {/* ----------------------------------------- */}

      {caseStatus === "ANALYZED" && (

        <div className="case-actions">

          <div>

            <span className="eyebrow">
              HUMAN REVIEW
            </span>

            <h3>
              Confirm the final case action.
            </h3>

          </div>


          <div className="action-buttons">

            <button
              className="contest-button"
              disabled={actionLoading}
              onClick={() =>
                handleAction("CONTEST")
              }
            >

              <Gavel size={17} />

              {actionLoading
                ? "Processing..."
                : "Contest Dispute"}

            </button>


            <button
              className="accept-button"
              disabled={actionLoading}
              onClick={() =>
                handleAction("ACCEPT")
              }
            >

              <Check size={17} />

              Accept Dispute

            </button>

          </div>

        </div>

      )}


      {/* ----------------------------------------- */}
      {/* ACTION RESULT */}
      {/* ----------------------------------------- */}

      {actionMessage && (

        <div className="action-message">

          <CheckCircle2 size={17} />

          {actionMessage}

        </div>

      )}


      {/* ----------------------------------------- */}
      {/* EVIDENCE */}
      {/* ----------------------------------------- */}

      <div className="evidence-section">

        <div className="section-title">

          <span>
            EVIDENCE SNAPSHOT
          </span>

          <span>
            {Object.keys(
              result.evidence || {}
            ).length} SIGNALS
          </span>

        </div>


        <div className="evidence-table-wrap">

          <table className="professional-table">

            <thead>

              <tr>

                <th>
                  Evidence Signal
                </th>

                <th>
                  Value
                </th>

              </tr>

            </thead>


            <tbody>

              {Object.entries(
                result.evidence || {}
              ).map(([key, value]) => (

                <tr key={key}>

                  <td>

                    {key
                      .replace(/_/g, " ")
                      .replace(
                        /\b\w/g,
                        (letter) =>
                          letter.toUpperCase()
                      )}

                  </td>


                  <td>

                    {typeof value === "boolean" ? (

                      <span
                        className={
                          value
                            ? "boolean-true"
                            : "boolean-false"
                        }
                      >

                        {value
                          ? "✓ Yes"
                          : "✕ No"}

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


      {/* ----------------------------------------- */}
      {/* GENERATED RESPONSE */}
      {/* ----------------------------------------- */}

      {result.draft_response && (

        <div className="draft-response">

          <div className="section-title">

            <span>
              GENERATED EVIDENCE RESPONSE
            </span>

            <span>
              AI ASSISTED DRAFT
            </span>

          </div>


          <div className="markdown-content">

            <ReactMarkdown>
              {result.draft_response}
            </ReactMarkdown>

          </div>

        </div>

      )}

    </section>
  );
}

function ResultMetric({ label, value }) {

  return (

    <div className="result-metric">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>

  );
}



/* =====================================================
   ANIMATED NUMBER
===================================================== */

function AnimatedNumber({
  value,
  suffix = "",
  duration = 900,
}) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let animationFrame;
    let startTime = null;

    const animate = (currentTime) => {
      if (startTime === null) {
        startTime = currentTime;
      }

      const progress = Math.min(
        (currentTime - startTime) / duration,
        1
      );

      // Smooth premium ease-out animation
      const easedProgress =
        1 - Math.pow(1 - progress, 3);

      setDisplayValue(value * easedProgress);

      if (progress < 1) {
        animationFrame =
          requestAnimationFrame(animate);
      }
    };

    animationFrame =
      requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [value, duration]);

  return (
    <>
      {Number.isInteger(value)
        ? Math.round(displayValue).toLocaleString()
        : displayValue.toFixed(1)}
      {suffix}
    </>
  );
}


/* =====================================================
   RECENT DISPUTE ROW
===================================================== */

function DisputeRow({
  id,
  reason,
  score,
  status,
}) {
  return (
    <div className="dispute-row">
      <div>
        <span className="transaction-id">
          {id}
        </span>

        <span className="reason">
          {reason}
        </span>
      </div>

      <div className="row-right">
        <span className="score">
          {score}
        </span>

        <span className="status">
          {status}
        </span>

        <ArrowUpRight size={17} />
      </div>
    </div>
  );
}


/* =====================================================
   INTELLIGENCE
===================================================== */

function Intelligence() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/metrics`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            "Failed to load metrics"
          );
        }

        return response.json();
      })
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);

        setError(
          "Could not load model metrics."
        );

        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <section className="page">
        <div className="hero compact">
          <p className="eyebrow">
            MODEL INTELLIGENCE
          </p>

          <h1>
            Loading metrics...
          </h1>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="page">
        <div className="hero compact">
          <p className="eyebrow">
            MODEL INTELLIGENCE
          </p>

          <h1>
            Metrics unavailable.
          </h1>

          <p className="hero-copy">
            {error}
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="hero compact">
        <p className="eyebrow">
          MODEL INTELLIGENCE
        </p>

        <h1>
          Honest metrics.
          <br />
          No black box.
        </h1>

        <p className="hero-copy">
          Performance measured on a held-out
          test set the model never trained on.
        </p>
      </div>

      <div className="metrics-grid">
        <Metric
          value={
            <AnimatedNumber
              value={metrics.precision * 100}
              suffix="%"
            />
          }
          label="Precision"
        />

        <Metric
          value={
            <AnimatedNumber
              value={metrics.recall * 100}
              suffix="%"
            />
          }
          label="Recall"
        />

        <Metric
          value={
            <AnimatedNumber
              value={metrics.roc_auc * 100}
              suffix="%"
            />
          }
          label="ROC-AUC"
        />

        <Metric
          value={
            <AnimatedNumber
              value={metrics.held_out_cases}
            />
          }
          label="Held-out cases"
        />
      </div>

      <div className="impact">
        <div>
          <span>FALSE-POSITIVE COST</span>

          <strong>
            ₹
            <AnimatedNumber
              value={metrics.false_positive_cost}
            />
          </strong>
        </div>

        <div>
          <span>MODELED RECOVEREY POTENTIAL</span>

          <strong>
            ₹
            <AnimatedNumber
              value={
                metrics.modeled_recovered_value
              }
            />
          </strong>
        </div>

        <div>
          <span>MODELED NET VALUE</span>

          <strong>
            ₹
            <AnimatedNumber
              value={metrics.net_modeled_value}
            />
          </strong>
        </div>
      </div>

      <div className="method-note">
        <Activity size={17} />

        <p>
          These metrics are served directly from
          the DisputeShield evaluation layer.
          Business impact figures are modeled
          estimates and should not be interpreted
          as measured financial outcomes.
        </p>
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
   AUDIT
===================================================== */

function Audit() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/audit`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load audit trail");
        }

        return response.json();
      })
      .then((data) => {
        setLogs([...data].reverse());
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load audit trail.");
        setLoading(false);
      });
  }, []);

  return (
    <section className="page">
      {/* KEEP THE ORIGINAL AUDIT LANDING PAGE */}
      <div className="hero compact">
        <p className="eyebrow">AUDIT TRAIL</p>

        <h1>
          Every decision
          <br />
          leaves a trail.
        </h1>

        <p className="hero-copy">
          Evidence, model confidence and actions are recorded
          for every dispute decision.
        </p>
      </div>
      <div className="audit-summary">

  <div>
    <span>RECORDED DECISIONS</span>
    <strong>
      {logs.length}
    </strong>
  </div>


  <div>
    <span>LAST UPDATED</span>
    <strong>
      {logs.length > 0
        ? new Date(
            logs[0].timestamp
          ).toLocaleTimeString()
        : "—"}
    </strong>
  </div>

</div>

      <div className="audit-table-section">
        <div className="section-heading audit-heading">
          <span>DECISION HISTORY</span>
          <span>{logs.length} RECORDS</span>
        </div>

        {loading && (
          <p className="audit-message">
            Loading audit trail...
          </p>
        )}

        {error && (
          <p className="audit-message">
            {error}
          </p>
        )}

        {!loading && !error && logs.length === 0 && (
          <p className="audit-message">
            No audit records yet. Analyze a dispute to create one.
          </p>
        )}

        {!loading && !error && logs.length > 0 && (
          <div className="audit-table-wrapper">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>TIME</th>
                  <th>TRANSACTION</th>
                  <th>REASON</th>
                  <th>ASSESSMENT</th>
                  <th>CONFIDENCE</th>
                  <th>ACTION</th>
                </tr>
              </thead>

              <tbody>
                {logs.map((log, index) => (
                  <tr
                    key={`${log.transaction_id}-${log.timestamp}-${index}`}
                    onClick={() => setSelectedLog(log)}
                    className="audit-row-clickable"
                  >
                    <td>
                      {log.timestamp
                        ? new Date(log.timestamp).toLocaleString()
                        : "—"}
                    </td>

                    <td className="transaction-cell">
                      {log.transaction_id || "—"}
                    </td>

                    <td>
                      {log.reason_code || "—"}
                    </td>

                    <td>
                      {log.assessment ||
                        log.prediction ||
                        "—"}
                    </td>

                    <td className="confidence-cell">
                      {log.confidence !== undefined
                        ? `${(Number(log.confidence) * 100).toFixed(1)}%`
                        : "—"}
                    </td>

                    <td>
                      <span className="action-pill">
                        {(log.action || "—").replaceAll("_", " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CLICKED AUDIT DETAIL */}
      {selectedLog && (
        <div className="audit-detail-overlay">
          <div className="audit-detail-card">

            <div className="detail-header">
              <div>
                <p className="eyebrow">AUDIT RECORD</p>
                <h2>{selectedLog.transaction_id}</h2>
              </div>

              <button
                className="close-button"
                onClick={() => setSelectedLog(null)}
              >
                ×
              </button>
            </div>

            <div className="detail-grid">

              <div className="detail-item">
                <span>TRANSACTION</span>
                <strong>{selectedLog.transaction_id || "—"}</strong>
              </div>

              <div className="detail-item">
                <span>REASON CODE</span>
                <strong>{selectedLog.reason_code || "—"}</strong>
              </div>

              <div className="detail-item">
                <span>ASSESSMENT</span>
                <strong>
                  {selectedLog.assessment ||
                    selectedLog.defensibility_label || "—"}
                </strong>
              </div>

              <div className="detail-item">
                <span>CONFIDENCE</span>
                <strong>
                  {selectedLog.confidence !== undefined
                    ? `${(Number(selectedLog.confidence) * 100).toFixed(1)}%`
                    : "—"}
                </strong>
              </div>

              <div className="detail-item">
                <span>RECOMMENDED ACTION</span>
                <strong>
                  {(selectedLog.action || "—").replaceAll("_", " ")}
                </strong>
              </div>

              <div className="detail-item">
                <span>TIME</span>
                <strong>
                  {selectedLog.timestamp
                    ? new Date(selectedLog.timestamp).toLocaleString()
                    : "—"}
                </strong>
              </div>

            </div>

            {selectedLog.evidence && (
              <div className="detail-evidence">
                <span>EVIDENCE SNAPSHOT</span>

                <div className="evidence-grid">
                  {Object.entries(selectedLog.evidence).map(
                    ([key, value]) => (
                      <div
                        className="evidence-item"
                        key={key}
                      >
                        <span>{key.replaceAll("_", " ")}</span>
                        <strong>{String(value)}</strong>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </section>
  );
}

/* =====================================================
   AUDIT EVENT
===================================================== */

function AuditEvent({ log, index }) {
  const date = new Date(log.timestamp);

  const time = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const actionText =
    log.action === "RECOMMEND_CONTEST"
      ? "Contest recommended"
      : log.action === "RECOMMEND_NOT_CONTESTING"
      ? "Not contesting recommended"
      : log.action || "Decision recorded";

  return (
    <div
      className="audit-event"
      style={{
        animationDelay: `${index * 0.08}s`,
      }}
    >
      <span className="audit-time">
        {time} UTC
      </span>

      <div className="audit-dot" />

      <div className="audit-content">
        <strong>
          {actionText}
        </strong>

        <span>
          {log.transaction_id} ·{" "}
          {log.confidence !== undefined
            ? `${(log.confidence * 100).toFixed(1)}% confidence`
            : "Confidence unavailable"}
        </span>

        <small>
          {log.defensibility_label || "—"} ·{" "}
          {log.reason_code || "—"}
        </small>
      </div>
    </div>
  );
}


export default App;