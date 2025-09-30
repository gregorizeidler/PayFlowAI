"""
Modelos de dados para o serviço de reconciliação
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class MatchType(Enum):
    RECEIVABLE = "receivable"
    PAYABLE = "payable"
    MANUAL = "manual"
    AUTOMATIC = "automatic"

class DiscrepancyType(Enum):
    AMOUNT_DIFFERENCE = "amount_difference"
    MISSING_TRANSACTION = "missing_transaction"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    DATE_MISMATCH = "date_mismatch"
    UNMATCHED_TRANSACTION = "unmatched_transaction"

class ReconciliationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"

@dataclass
class BankTransaction:
    """Transação bancária extraída do extrato"""
    id: str
    date: date
    amount: Decimal
    description: str
    type: str  # credit, debit
    reference: Optional[str] = None
    account_id: Optional[str] = None
    source: str = "unknown"  # ofx, csv, pdf
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": float(self.amount),
            "description": self.description,
            "type": self.type,
            "reference": self.reference,
            "account_id": self.account_id,
            "source": self.source,
            "raw_data": self.raw_data
        }

@dataclass
class TransactionMatch:
    """Match entre transação bancária e fatura"""
    transaction_id: str
    invoice_id: str
    confidence_score: float
    match_type: str
    matched_amount: Decimal
    match_reason: str
    matched_at: datetime
    matched_by: Optional[str] = None  # user_id para matches manuais
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "invoice_id": self.invoice_id,
            "confidence_score": self.confidence_score,
            "match_type": self.match_type,
            "matched_amount": float(self.matched_amount),
            "match_reason": self.match_reason,
            "matched_at": self.matched_at.isoformat(),
            "matched_by": self.matched_by
        }

@dataclass
class Discrepancy:
    """Discrepância detectada na conciliação"""
    id: str
    discrepancy_type: str
    transaction_id: Optional[str] = None
    invoice_id: Optional[str] = None
    expected_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    description: str = ""
    severity: str = "medium"  # low, medium, high
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "discrepancy_type": self.discrepancy_type,
            "transaction_id": self.transaction_id,
            "invoice_id": self.invoice_id,
            "expected_amount": float(self.expected_amount) if self.expected_amount else None,
            "actual_amount": float(self.actual_amount) if self.actual_amount else None,
            "difference": float(self.difference) if self.difference else None,
            "description": self.description,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes
        }

@dataclass
class ReconciliationResult:
    """Resultado completo de uma conciliação"""
    bank_account_id: str
    period_start: date
    period_end: date
    status: str
    processed_at: datetime
    
    # Estatísticas
    total_transactions: int = 0
    matched_transactions: int = 0
    unmatched_transactions: int = 0
    total_amount_processed: Decimal = field(default_factory=lambda: Decimal('0'))
    matched_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # Resultados detalhados
    matches: List[TransactionMatch] = field(default_factory=list)
    discrepancies: List[Discrepancy] = field(default_factory=list)
    unmatched_bank_transactions: List[BankTransaction] = field(default_factory=list)
    
    # Metadados
    processing_time_seconds: Optional[float] = None
    algorithm_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bank_account_id": self.bank_account_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status,
            "processed_at": self.processed_at.isoformat(),
            "statistics": {
                "total_transactions": self.total_transactions,
                "matched_transactions": self.matched_transactions,
                "unmatched_transactions": self.unmatched_transactions,
                "matching_rate": (self.matched_transactions / self.total_transactions * 100) if self.total_transactions > 0 else 0,
                "total_amount_processed": float(self.total_amount_processed),
                "matched_amount": float(self.matched_amount)
            },
            "matches": [m.to_dict() for m in self.matches],
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "unmatched_transactions": [t.to_dict() for t in self.unmatched_bank_transactions],
            "metadata": {
                "processing_time_seconds": self.processing_time_seconds,
                "algorithm_version": self.algorithm_version
            }
        }

@dataclass
class MatchCandidate:
    """Candidato para matching com score"""
    invoice_id: str
    invoice_data: Dict[str, Any]
    confidence_score: float
    match_reasons: List[str]
    score_breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "invoice_data": self.invoice_data,
            "confidence_score": self.confidence_score,
            "match_reasons": self.match_reasons,
            "score_breakdown": self.score_breakdown
        }

@dataclass
class ReconciliationRule:
    """Regra de conciliação configurável"""
    name: str
    enabled: bool
    priority: int
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "conditions": self.conditions,
            "actions": self.actions
        }

# Enums para status e tipos
class TransactionType(Enum):
    CREDIT = "credit"
    DEBIT = "debit"

class MatchConfidence(Enum):
    HIGH = "high"      # >= 0.9
    MEDIUM = "medium"  # 0.7 - 0.89
    LOW = "low"        # 0.5 - 0.69
    VERY_LOW = "very_low"  # < 0.5

class ProcessingStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
