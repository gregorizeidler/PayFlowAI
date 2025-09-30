"""
Modelos de dados para o workflow de AR
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum

class InvoiceStatus(Enum):
    CREATING = "creating"
    VALIDATION_FAILED = "validation_failed"
    GENERATION_FAILED = "generation_failed"
    ACTIVE = "active"
    OVERDUE = "overdue"
    PARTIAL_PAYMENT = "partial_payment"
    PAID = "paid"
    CANCELLED = "cancelled"
    ERROR = "error"

class NotificationMethod(Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    REGISTERED_MAIL = "registered_mail"
    WHATSAPP = "whatsapp"

class DunningStage(Enum):
    REMINDER = "reminder"
    FIRST_NOTICE = "first_notice"
    SECOND_NOTICE = "second_notice"
    FINAL_NOTICE = "final_notice"
    LEGAL_ACTION = "legal_action"

@dataclass
class DunningRule:
    """Regra de cobrança automatizada"""
    name: str
    trigger_days: int  # Dias relativos ao vencimento (negativo = antes, positivo = depois)
    notification_methods: List[NotificationMethod]
    template: str
    priority: int
    max_attempts: int = 3
    cooldown_hours: int = 24
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trigger_days": self.trigger_days,
            "notification_methods": [method.value for method in self.notification_methods],
            "template": self.template,
            "priority": self.priority,
            "max_attempts": self.max_attempts,
            "cooldown_hours": self.cooldown_hours
        }

@dataclass
class DunningResult:
    """Resultado de uma tentativa de cobrança"""
    invoice_id: str
    action_taken: str
    notification_sent: bool
    notification_methods: List[str] = field(default_factory=list)
    rule_applied: Optional[str] = None
    days_overdue: Optional[int] = None
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "action_taken": self.action_taken,
            "notification_sent": self.notification_sent,
            "notification_methods": self.notification_methods,
            "rule_applied": self.rule_applied,
            "days_overdue": self.days_overdue,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error": self.error,
            "reason": self.reason
        }

@dataclass
class PaymentMethod:
    """Método de pagamento gerado"""
    type: str  # boleto, pix, credit_card, bank_transfer
    identifier: str  # código de barras, chave PIX, etc.
    qr_code: Optional[str] = None
    expiry_date: Optional[date] = None
    instructions: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "identifier": self.identifier,
            "qr_code": self.qr_code,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "instructions": self.instructions
        }

@dataclass
class ARWorkflow:
    """Estado completo do workflow de uma fatura AR"""
    invoice_id: str
    invoice_data: Dict[str, Any]
    status: str
    created_at: datetime
    
    # Resultados dos processamentos
    validation_result: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None
    payment_methods: List[PaymentMethod] = field(default_factory=list)
    
    # Informações de envio
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    
    # Cobrança
    dunning_schedule: Optional[Dict[str, Any]] = None
    dunning_attempts: List[DunningResult] = field(default_factory=list)
    
    # Pagamento
    due_date: Optional[date] = None
    paid_amount: float = 0.0
    payment_date: Optional[date] = None
    
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
            "pdf_path": self.pdf_path,
            "payment_methods": [pm.to_dict() for pm in self.payment_methods],
            "email_sent": self.email_sent,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "dunning_schedule": self.dunning_schedule,
            "dunning_attempts": [da.to_dict() for da in self.dunning_attempts],
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_amount": self.paid_amount,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

@dataclass
class CustomerProfile:
    """Perfil de cobrança do cliente"""
    customer_id: str
    payment_behavior: str  # good, average, poor
    average_payment_days: float
    total_invoices: int
    total_paid: float
    overdue_count: int
    preferred_contact_method: NotificationMethod
    last_payment_date: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "payment_behavior": self.payment_behavior,
            "average_payment_days": self.average_payment_days,
            "total_invoices": self.total_invoices,
            "total_paid": self.total_paid,
            "overdue_count": self.overdue_count,
            "preferred_contact_method": self.preferred_contact_method.value,
            "last_payment_date": self.last_payment_date.isoformat() if self.last_payment_date else None
        }

# Estados de cobrança
class DunningStatus(Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Tipos de notificação
class NotificationType(Enum):
    REMINDER = "reminder"
    DUE_NOTICE = "due_notice"
    OVERDUE_NOTICE = "overdue_notice"
    FINAL_NOTICE = "final_notice"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    THANK_YOU = "thank_you"
