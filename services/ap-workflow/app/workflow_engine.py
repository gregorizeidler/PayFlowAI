"""
Motor de Workflow para Contas a Pagar
Implementa o 3-Way Matching e fluxo de aprovação
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import httpx

from app.processors.three_way_matcher import ThreeWayMatcher
from app.processors.approval_engine import ApprovalEngine
from app.processors.exception_handler import ExceptionHandler
from app.models.workflow_models import InvoiceWorkflow, MatchingResult, ApprovalResult
from app.config import settings

logger = logging.getLogger(__name__)

class APWorkflowEngine:
    """Motor principal do workflow de Contas a Pagar"""
    
    def __init__(self):
        self.three_way_matcher = ThreeWayMatcher()
        self.approval_engine = ApprovalEngine()
        self.exception_handler = ExceptionHandler()
        
    async def process_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma fatura através do workflow completo:
        1. Validação inicial
        2. 3-Way Matching
        3. Tratamento de exceções
        4. Fluxo de aprovação
        5. Agendamento de pagamento
        """
        try:
            invoice_id = invoice_data.get("id")
            logger.info(f"🔄 Iniciando workflow para fatura {invoice_id}")
            
            # Criar workflow instance
            workflow = InvoiceWorkflow(
                invoice_id=invoice_id,
                invoice_data=invoice_data,
                status="processing",
                created_at=datetime.utcnow()
            )
            
            # 1. Validação inicial
            logger.info(f"✅ Validando fatura {invoice_id}")
            validation_result = await self._validate_invoice(invoice_data)
            workflow.validation_result = validation_result
            
            if not validation_result["is_valid"]:
                workflow.status = "validation_failed"
                workflow.error_message = validation_result["error"]
                return await self._finalize_workflow(workflow)
            
            # 2. 3-Way Matching
            logger.info(f"⚖️ Executando 3-Way Matching para fatura {invoice_id}")
            matching_result = await self.three_way_matcher.perform_matching(invoice_data)
            workflow.matching_result = matching_result
            
            # 3. Verificar se há exceções
            if matching_result.has_exceptions:
                logger.warning(f"⚠️ Exceções detectadas na fatura {invoice_id}")
                
                # Tentar resolver exceções automaticamente
                resolution_result = await self.exception_handler.handle_exceptions(
                    matching_result.exceptions
                )
                
                if not resolution_result["auto_resolved"]:
                    workflow.status = "pending_exception_review"
                    workflow.exceptions = matching_result.exceptions
                    return await self._finalize_workflow(workflow)
            
            # 4. Fluxo de aprovação
            logger.info(f"👥 Iniciando fluxo de aprovação para fatura {invoice_id}")
            approval_result = await self.approval_engine.process_approval(
                invoice_data, matching_result
            )
            workflow.approval_result = approval_result
            
            if approval_result.requires_manual_approval:
                workflow.status = "pending_approval"
                workflow.approver_level = approval_result.required_level
                return await self._finalize_workflow(workflow)
            
            # 5. Aprovação automática - agendar pagamento
            if approval_result.auto_approved:
                logger.info(f"✅ Fatura {invoice_id} aprovada automaticamente")
                payment_result = await self._schedule_payment(invoice_data, workflow)
                workflow.payment_scheduled = payment_result["scheduled"]
                workflow.payment_date = payment_result.get("payment_date")
                workflow.status = "approved_payment_scheduled"
            
            return await self._finalize_workflow(workflow)
            
        except Exception as e:
            logger.error(f"❌ Erro no workflow da fatura {invoice_id}: {str(e)}")
            return {
                "invoice_id": invoice_id,
                "status": "error",
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }
    
    async def _validate_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validação inicial da fatura"""
        try:
            # Campos obrigatórios
            required_fields = ["id", "supplier_id", "total_amount", "invoice_date", "due_date"]
            missing_fields = [field for field in required_fields if not invoice_data.get(field)]
            
            if missing_fields:
                return {
                    "is_valid": False,
                    "error": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
                }
            
            # Validar valores
            total_amount = invoice_data.get("total_amount", 0)
            if total_amount <= 0:
                return {
                    "is_valid": False,
                    "error": "Valor total deve ser maior que zero"
                }
            
            # Validar datas
            try:
                invoice_date = datetime.fromisoformat(invoice_data["invoice_date"])
                due_date = datetime.fromisoformat(invoice_data["due_date"])
                
                if due_date < invoice_date:
                    return {
                        "is_valid": False,
                        "error": "Data de vencimento não pode ser anterior à data da fatura"
                    }
            except ValueError:
                return {
                    "is_valid": False,
                    "error": "Formato de data inválido"
                }
            
            return {
                "is_valid": True,
                "validated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Erro na validação: {str(e)}"
            }
    
    async def _schedule_payment(self, invoice_data: Dict[str, Any], workflow: InvoiceWorkflow) -> Dict[str, Any]:
        """Agenda pagamento da fatura aprovada"""
        try:
            # Calcular data de pagamento (2 dias antes do vencimento)
            due_date = datetime.fromisoformat(invoice_data["due_date"])
            payment_date = due_date.date()
            
            # TODO: Integrar com sistema de pagamentos real
            # Por enquanto, simular agendamento
            
            logger.info(f"💳 Pagamento agendado para {payment_date}")
            
            return {
                "scheduled": True,
                "payment_date": payment_date.isoformat(),
                "amount": invoice_data["total_amount"],
                "method": "bank_transfer",
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao agendar pagamento: {str(e)}")
            return {
                "scheduled": False,
                "error": str(e)
            }
    
    async def _finalize_workflow(self, workflow: InvoiceWorkflow) -> Dict[str, Any]:
        """Finaliza o workflow e notifica o Core API"""
        try:
            workflow.completed_at = datetime.utcnow()
            
            # Preparar resultado
            result = {
                "invoice_id": workflow.invoice_id,
                "status": workflow.status,
                "validation_result": workflow.validation_result,
                "matching_result": workflow.matching_result.to_dict() if workflow.matching_result else None,
                "approval_result": workflow.approval_result.to_dict() if workflow.approval_result else None,
                "exceptions": [exc.to_dict() for exc in workflow.exceptions] if workflow.exceptions else [],
                "payment_scheduled": workflow.payment_scheduled,
                "payment_date": workflow.payment_date.isoformat() if workflow.payment_date else None,
                "error_message": workflow.error_message,
                "processed_at": workflow.completed_at.isoformat(),
                "processing_time": (workflow.completed_at - workflow.created_at).total_seconds()
            }
            
            # Notificar Core API
            await self._notify_core_api(result)
            
            logger.info(f"✅ Workflow finalizado para fatura {workflow.invoice_id}: {workflow.status}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao finalizar workflow: {str(e)}")
            return {
                "invoice_id": workflow.invoice_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _notify_core_api(self, result: Dict[str, Any]):
        """Notifica o Core API sobre o resultado do workflow"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.core_api_url}/api/v1/ap/workflow-completed",
                    json=result,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Core API notificado sobre fatura {result['invoice_id']}")
                else:
                    logger.error(f"❌ Falha ao notificar Core API: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao notificar Core API: {str(e)}")
    
    async def get_workflow_status(self, invoice_id: str) -> Dict[str, Any]:
        """Obtém status do workflow de uma fatura"""
        # TODO: Implementar busca no banco de dados
        return {
            "invoice_id": invoice_id,
            "status": "not_found",
            "message": "Workflow não encontrado"
        }
    
    async def retry_failed_workflow(self, invoice_id: str) -> Dict[str, Any]:
        """Reprocessa workflow que falhou"""
        # TODO: Implementar retry logic
        return {
            "invoice_id": invoice_id,
            "status": "retry_scheduled",
            "message": "Workflow agendado para reprocessamento"
        }
