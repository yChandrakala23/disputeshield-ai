from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EvidenceSnapshot(BaseModel):
    amount_inr: float
    reason_code: str
    delivery_confirmed: bool
    tracking_matches_address: bool
    signed_delivery_proof: bool
    device_matches_prior_orders: bool
    ip_geo_matches_billing: bool
    customer_prior_clean_orders: int
    support_ticket_exists: bool
    duplicate_txn_id_found: bool
    subscription_cancel_logged: bool
    days_since_transaction: int
    is_contradictory: bool = False
    completeness_score: float = 1.0


class DecisionOutput(BaseModel):
    action: str
    reason: str
    requires_human_review: bool
    confidence: float
    defensibility_label: str
    policy_checks: Dict[str, Any] = Field(default_factory=dict)


class ProcessDisputeResponse(BaseModel):
    transaction_id: str
    merchant_id: str = "MERCH_DEFAULT"
    evidence: Dict[str, Any]
    prediction: str
    confidence: float
    brier_score: Optional[float] = None
    decision: DecisionOutput
    draft_response: Optional[str] = None
    draft_status: str = "TEMPLATE_FALLBACK"
    case_status: str
    human_action: Optional[str] = None
    override_reason: Optional[str] = None
    response_deadline: str
    audit_id: Optional[int] = None


class AnalystActionRequest(BaseModel):
    action: str = Field(..., description="Action must be CONTEST or ACCEPT")
    override_reason: Optional[str] = Field(None, description="Reason for analyst override")
    analyst_id: Optional[str] = "analyst_default"


class AnalystActionResponse(BaseModel):
    transaction_id: str
    action: str
    status: str
    override_reason: Optional[str] = None
    timestamp: str


class BenchmarkMetric(BaseModel):
    model_name: str = "Model"
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    brier_score: float
    net_value_inr: float


class MetricsResponse(BaseModel):
    current_model: str
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    brier_score: float
    held_out_cases: int
    optimal_threshold: float
    false_positive_cost_inr: float
    recovered_value_inr: float
    net_value_inr: float
    benchmarks: Dict[str, BenchmarkMetric] = Field(default_factory=dict)
    note: str


class SimulateDisputeRequest(BaseModel):
    amount_inr: float = 1500.0
    reason_code: str = "item_not_received"
    delivery_confirmed: bool = True
    tracking_matches_address: bool = True
    signed_delivery_proof: bool = True
    device_matches_prior_orders: bool = True
    ip_geo_matches_billing: bool = True
    customer_prior_clean_orders: int = 3
    support_ticket_exists: bool = False
    duplicate_txn_id_found: bool = False
    subscription_cancel_logged: bool = False
    days_since_transaction: int = 15
    is_contradictory: bool = False


class SimulateDisputeResponse(BaseModel):
    prediction: str
    confidence: float
    decision: DecisionOutput
    completeness_score: float
    is_simulation: bool = True
