"""
Modelos de dados para o workflow de AP
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum

class ExceptionSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ApprovalLevel(Enum):
    AUTO = "auto"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"

@dataclass
class MatchingException:
    """Exceção detectada no 3-way matching"""
    type: str
    description: str
    severity: str
    variance_amount: Optional[float] = None
    variance_percent: Optional[float] = None
    field_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "severity": self.severity,
            "variance_amount": self.variance_amount,
            "variance_percent": self.variance_percent,
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value
        }

@dataclass
class MatchingResult:
    """Resultado do 3-way matching"""
    invoice_id: str
    matched: bool
    has_exceptions: bool
    exceptions: List[MatchingException] = field(default_factory=list)
    purchase_order_id: Optional[str] = None
    goods_receipt_id: Optional[str] = None
    matching_score: float = 0.0
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "matched": self.matched,
            "has_exceptions": self.has_exceptions,
            "exceptions": [exc.to_dict() for exc in self.exceptions],
            "purchase_order_id": self.purchase_order_id,
            "goods_receipt_id": self.goods_receipt_id,
            "matching_score": self.matching_score,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error": self.error
        }

@dataclass
class ApprovalResult:
    """Resultado do processo de aprovação"""
    invoice_id: str
    auto_approved: bool
    requires_manual_approval: bool
    required_level: Optional[str] = None
    approver_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "auto_approved": self.auto_approved,
            "requires_manual_approval": self.requires_manual_approval,
            "required_level": self.required_level,
            "approver_id": self.approver_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approval_reason": self.approval_reason,
            "rejection_reason": self.rejection_reason
        }

@dataclass
class InvoiceWorkflow:
    """Estado completo do workflow de uma fatura"""
    invoice_id: str
    invoice_data: Dict[str, Any]
    status: str
    created_at: datetime
    
    # Resultados dos processamentos
    validation_result: Optional[Dict[str, Any]] = None
    matching_result: Optional[MatchingResult] = None
    approval_result: Optional[ApprovalResult] = None
    exceptions: List[MatchingException] = field(default_factory=list)
    
    # Informações de aprovação
    approver_level: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Informações de pagamento
    payment_scheduled: bool = False
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    
    # Controle de erro
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Timestamps
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "validation_result": self.validation_result,
            "matching_result": self.matching_result.to_dict() if self.matching_result else None,
            "approval_result": self.approval_result.to_dict() if self.approval_result else None,
            "exceptions": [exc.to_dict() for exc in self.exceptions],
            "approver_level": self.approver_level,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "payment_scheduled": self.payment_scheduled,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

# Estados possíveis do workflow
class WorkflowStatus(Enum):
    PROCESSING = "processing"
    VALIDATION_FAILED = "validation_failed"
    PENDING_EXCEPTION_REVIEW = "pending_exception_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED_PAYMENT_SCHEDULED = "approved_payment_scheduled"
    REJECTED = "rejected"
    ERROR = "error"
    COMPLETED = "completed"

# Tipos de exceções do 3-way matching
class ExceptionType(Enum):
    NO_PURCHASE_ORDER = "no_purchase_order"
    NO_GOODS_RECEIPT = "no_goods_receipt"
    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    QUANTITY_OVER_RECEIPT = "quantity_over_receipt"
    DATE_SEQUENCE_ERROR = "date_sequence_error"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    PROCESSING_ERROR = "processing_error"
