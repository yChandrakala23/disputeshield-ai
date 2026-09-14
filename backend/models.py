from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from backend.database import Base


class DisputeRecord(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    merchant_id = Column(String(64), default="MERCH_DEFAULT", index=True)
    amount_inr = Column(Float, nullable=False)
    reason_code = Column(String(64), nullable=False)
    case_status = Column(String(32), default="RECEIVED", index=True)  # RECEIVED, ANALYZING, HUMAN_REVIEW, CONTESTED, ACCEPTED
    response_deadline = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    evidence = relationship("EvidenceRecord", back_populates="dispute", uselist=False, cascade="all, delete-orphan")
    decision = relationship("DecisionRecord", back_populates="dispute", uselist=False, cascade="all, delete-orphan")
    actions = relationship("AnalystActionRecord", back_populates="dispute", cascade="all, delete-orphan")


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    transaction_id = Column(String(64), index=True, nullable=False)
    evidence_json = Column(Text, nullable=False)  # JSON string
    completeness_score = Column(Float, default=1.0)
    is_contradictory = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dispute = relationship("DisputeRecord", back_populates="evidence")

    def get_payload(self) -> dict:
        return json.loads(self.evidence_json) if self.evidence_json else {}


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    transaction_id = Column(String(64), index=True, nullable=False)
    model_version = Column(String(32), default="rf_v2.0")
    defensibility_label = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    brier_score = Column(Float, nullable=True)
    policy_action = Column(String(64), nullable=False)
    policy_reason = Column(Text, nullable=False)
    draft_response = Column(Text, nullable=True)
    draft_status = Column(String(32), default="TEMPLATE_FALLBACK")  # GROUNDED_LLM, TEMPLATE_FALLBACK, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dispute = relationship("DisputeRecord", back_populates="decision")


class AnalystActionRecord(Base):
    __tablename__ = "analyst_actions"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False)
    transaction_id = Column(String(64), index=True, nullable=False)
    original_recommendation = Column(String(64), nullable=False)
    action_taken = Column(String(32), nullable=False)  # CONTEST, ACCEPT
    override_reason = Column(String(128), nullable=True)
    analyst_id = Column(String(64), default="analyst_default")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dispute = relationship("DisputeRecord", back_populates="actions")


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class MLMetricRecord(Base):
    __tablename__ = "ml_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(64), nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    brier_score = Column(Float, nullable=False)
    optimal_threshold = Column(Float, default=0.65)
    net_value_inr = Column(Float, nullable=False)
    n_test_samples = Column(Integer, nullable=False)
    evaluated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
