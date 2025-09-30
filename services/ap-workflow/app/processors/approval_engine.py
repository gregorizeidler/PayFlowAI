"""
Motor de Aprovação para Contas a Pagar
Implementa regras de aprovação baseadas em valor e exceções
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.models.workflow_models import ApprovalResult, MatchingResult, ApprovalLevel
from app.config import settings

logger = logging.getLogger(__name__)

class ApprovalEngine:
    """Motor de aprovação automática e manual"""
    
    def __init__(self):
        self.auto_approval_limit = Decimal(str(settings.auto_approval_limit))
        self.manager_approval_limit = Decimal(str(settings.manager_approval_limit))
        self.director_approval_limit = Decimal(str(settings.director_approval_limit))
    
    async def process_approval(self, invoice_data: Dict[str, Any], matching_result: MatchingResult) -> ApprovalResult:
        """
        Processa aprovação da fatura baseado em:
        1. Valor da fatura
        2. Resultado do 3-way matching
        3. Histórico do fornecedor
        4. Regras de negócio configuradas
        """
        try:
            invoice_id = invoice_data.get("id")
            total_amount = Decimal(str(invoice_data.get("total_amount", 0)))
            
            logger.info(f"👥 Processando aprovação para fatura {invoice_id} - Valor: R$ {total_amount}")
            
            # 1. Verificar se tem exceções críticas
            if matching_result.has_exceptions:
                critical_exceptions = self._has_critical_exceptions(matching_result.exceptions)
                if critical_exceptions:
                    return ApprovalResult(
                        invoice_id=invoice_id,
                        auto_approved=False,
                        requires_manual_approval=True,
                        required_level=ApprovalLevel.MANAGER.value,
                        approval_reason="Exceções críticas detectadas no 3-way matching"
                    )
            
            # 2. Verificar limites de aprovação automática
            if total_amount <= self.auto_approval_limit and matching_result.matching_score >= 95.0:
                return ApprovalResult(
                    invoice_id=invoice_id,
                    auto_approved=True,
                    requires_manual_approval=False,
                    approved_at=datetime.utcnow(),
                    approval_reason=f"Aprovação automática - Valor: R$ {total_amount}, Score: {matching_result.matching_score}%"
                )
            
            # 3. Determinar nível de aprovação necessário
            required_level = self._determine_approval_level(total_amount, matching_result)
            
            return ApprovalResult(
                invoice_id=invoice_id,
                auto_approved=False,
                requires_manual_approval=True,
                required_level=required_level,
                approval_reason=f"Aprovação manual necessária - Valor: R$ {total_amount}"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro no processo de aprovação: {str(e)}")
            return ApprovalResult(
                invoice_id=invoice_id,
                auto_approved=False,
                requires_manual_approval=True,
                required_level=ApprovalLevel.MANAGER.value,
                rejection_reason=f"Erro no processamento: {str(e)}"
            )
    
    def _has_critical_exceptions(self, exceptions) -> bool:
        """Verifica se há exceções que impedem aprovação automática"""
        critical_types = [
            "no_purchase_order",
            "supplier_mismatch",
            "quantity_over_receipt"
        ]
        
        for exception in exceptions:
            if exception.type in critical_types:
                return True
            
            # Exceções de alta severidade também são críticas
            if exception.severity == "high":
                return True
        
        return False
    
    def _determine_approval_level(self, amount: Decimal, matching_result: MatchingResult) -> str:
        """Determina o nível de aprovação necessário"""
        
        # Ajustar nível baseado no matching score
        score_penalty = 0
        if matching_result.matching_score < 90:
            score_penalty = 1  # Elevar um nível
        elif matching_result.matching_score < 80:
            score_penalty = 2  # Elevar dois níveis
        
        # Determinar nível base por valor
        if amount <= self.manager_approval_limit:
            base_level = 1  # Supervisor
        elif amount <= self.director_approval_limit:
            base_level = 2  # Manager
        else:
            base_level = 3  # Director
        
        # Aplicar penalidade
        final_level = min(3, base_level + score_penalty)
        
        level_map = {
            1: ApprovalLevel.SUPERVISOR.value,
            2: ApprovalLevel.MANAGER.value,
            3: ApprovalLevel.DIRECTOR.value
        }
        
        return level_map.get(final_level, ApprovalLevel.DIRECTOR.value)
    
    async def approve_invoice(self, invoice_id: str, approver_id: str, comments: Optional[str] = None) -> ApprovalResult:
        """Aprova fatura manualmente"""
        try:
            logger.info(f"✅ Aprovando fatura {invoice_id} por {approver_id}")
            
            return ApprovalResult(
                invoice_id=invoice_id,
                auto_approved=False,
                requires_manual_approval=False,
                approver_id=approver_id,
                approved_at=datetime.utcnow(),
                approval_reason=comments or "Aprovação manual"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao aprovar fatura: {str(e)}")
            raise
    
    async def reject_invoice(self, invoice_id: str, approver_id: str, reason: str) -> ApprovalResult:
        """Rejeita fatura manualmente"""
        try:
            logger.info(f"❌ Rejeitando fatura {invoice_id} por {approver_id}")
            
            return ApprovalResult(
                invoice_id=invoice_id,
                auto_approved=False,
                requires_manual_approval=False,
                approver_id=approver_id,
                approved_at=datetime.utcnow(),
                rejection_reason=reason
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao rejeitar fatura: {str(e)}")
            raise
    
    async def get_pending_approvals(self, approver_level: str) -> List[Dict[str, Any]]:
        """Obtém faturas pendentes de aprovação para um nível"""
        # TODO: Implementar busca no banco de dados
        return [
            {
                "invoice_id": "inv-001",
                "supplier_name": "Fornecedor ABC",
                "amount": 5500.00,
                "due_date": "2024-01-15",
                "matching_score": 87.5,
                "exceptions_count": 2,
                "pending_since": "2024-01-10T10:30:00"
            }
        ]
    
    def get_approval_rules(self) -> Dict[str, Any]:
        """Retorna regras de aprovação configuradas"""
        return {
            "auto_approval_limit": float(self.auto_approval_limit),
            "manager_approval_limit": float(self.manager_approval_limit),
            "director_approval_limit": float(self.director_approval_limit),
            "minimum_matching_score": 95.0,
            "critical_exception_types": [
                "no_purchase_order",
                "supplier_mismatch", 
                "quantity_over_receipt"
            ]
        }
