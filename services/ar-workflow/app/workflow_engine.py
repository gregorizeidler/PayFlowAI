"""
Motor de Workflow para Contas a Receber
Implementa criação de faturas, cobrança automatizada e controle de inadimplência
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import httpx

from app.processors.invoice_generator import InvoiceGenerator
from app.processors.dunning_engine import DunningEngine
from app.processors.payment_processor import PaymentProcessor
from app.models.ar_models import ARWorkflow, InvoiceStatus, DunningResult
from app.config import settings

logger = logging.getLogger(__name__)

class ARWorkflowEngine:
    """Motor principal do workflow de Contas a Receber"""
    
    def __init__(self):
        self.invoice_generator = InvoiceGenerator()
        self.dunning_engine = DunningEngine()
        self.payment_processor = PaymentProcessor()
        
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova fatura e inicia o workflow AR:
        1. Validação dos dados
        2. Geração do PDF da fatura
        3. Geração do boleto/PIX
        4. Envio por email
        5. Agendamento de lembretes
        """
        try:
            invoice_id = invoice_data.get("id")
            logger.info(f"📄 Criando fatura {invoice_id}")
            
            # Criar workflow instance
            workflow = ARWorkflow(
                invoice_id=invoice_id,
                invoice_data=invoice_data,
                status=InvoiceStatus.CREATING.value,
                created_at=datetime.utcnow()
            )
            
            # 1. Validação inicial
            logger.info(f"✅ Validando dados da fatura {invoice_id}")
            validation_result = await self._validate_invoice_data(invoice_data)
            workflow.validation_result = validation_result
            
            if not validation_result["is_valid"]:
                workflow.status = InvoiceStatus.VALIDATION_FAILED.value
                workflow.error_message = validation_result["error"]
                return await self._finalize_workflow(workflow)
            
            # 2. Gerar PDF da fatura
            logger.info(f"📄 Gerando PDF da fatura {invoice_id}")
            pdf_result = await self.invoice_generator.generate_invoice_pdf(invoice_data)
            workflow.pdf_path = pdf_result.get("pdf_path")
            
            if not pdf_result["success"]:
                workflow.status = InvoiceStatus.GENERATION_FAILED.value
                workflow.error_message = pdf_result["error"]
                return await self._finalize_workflow(workflow)
            
            # 3. Gerar boleto/PIX
            logger.info(f"💳 Gerando meios de pagamento para fatura {invoice_id}")
            payment_result = await self.payment_processor.generate_payment_methods(invoice_data)
            workflow.payment_methods = payment_result
            
            # 4. Enviar fatura por email
            logger.info(f"📧 Enviando fatura {invoice_id} por email")
            email_result = await self._send_invoice_email(invoice_data, workflow)
            workflow.email_sent = email_result["sent"]
            workflow.email_sent_at = datetime.utcnow() if email_result["sent"] else None
            
            # 5. Agendar lembretes de cobrança
            logger.info(f"⏰ Agendando lembretes para fatura {invoice_id}")
            dunning_schedule = await self.dunning_engine.schedule_dunning_sequence(invoice_data)
            workflow.dunning_schedule = dunning_schedule
            
            # Marcar como ativa
            workflow.status = InvoiceStatus.ACTIVE.value
            workflow.due_date = datetime.fromisoformat(invoice_data["due_date"]).date()
            
            return await self._finalize_workflow(workflow)
            
        except Exception as e:
            logger.error(f"❌ Erro no workflow da fatura {invoice_id}: {str(e)}")
            return {
                "invoice_id": invoice_id,
                "status": "error",
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }
    
    async def process_payment_received(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa pagamento recebido:
        1. Identifica a fatura
        2. Valida o valor
        3. Marca como paga
        4. Cancela cobranças pendentes
        """
        try:
            invoice_id = payment_data.get("invoice_id")
            amount_paid = Decimal(str(payment_data.get("amount", 0)))
            
            logger.info(f"💰 Processando pagamento para fatura {invoice_id}: R$ {amount_paid}")
            
            # Buscar fatura
            invoice_data = await self._get_invoice_data(invoice_id)
            if not invoice_data:
                return {"error": "Fatura não encontrada"}
            
            invoice_amount = Decimal(str(invoice_data.get("total_amount", 0)))
            
            # Verificar valor
            if amount_paid >= invoice_amount:
                # Pagamento completo
                await self._mark_invoice_as_paid(invoice_id, payment_data)
                await self.dunning_engine.cancel_dunning_sequence(invoice_id)
                
                logger.info(f"✅ Fatura {invoice_id} marcada como paga")
                
                return {
                    "invoice_id": invoice_id,
                    "status": "paid",
                    "amount_paid": float(amount_paid),
                    "payment_date": payment_data.get("payment_date"),
                    "dunning_cancelled": True
                }
            else:
                # Pagamento parcial
                await self._record_partial_payment(invoice_id, payment_data)
                
                logger.info(f"💰 Pagamento parcial registrado para fatura {invoice_id}")
                
                return {
                    "invoice_id": invoice_id,
                    "status": "partial_payment",
                    "amount_paid": float(amount_paid),
                    "remaining_amount": float(invoice_amount - amount_paid),
                    "payment_date": payment_data.get("payment_date")
                }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar pagamento: {str(e)}")
            return {"error": str(e)}
    
    async def send_dunning_notification(self, customer_id: str) -> Dict[str, Any]:
        """Envia notificação de cobrança para um cliente"""
        try:
            logger.info(f"📢 Enviando cobrança para cliente {customer_id}")
            
            # Buscar faturas em atraso do cliente
            overdue_invoices = await self._get_overdue_invoices(customer_id)
            
            if not overdue_invoices:
                return {
                    "customer_id": customer_id,
                    "status": "no_overdue_invoices",
                    "message": "Nenhuma fatura em atraso encontrada"
                }
            
            # Enviar cobrança
            dunning_result = await self.dunning_engine.send_dunning_notification(
                customer_id, overdue_invoices
            )
            
            return {
                "customer_id": customer_id,
                "status": "sent",
                "invoices_count": len(overdue_invoices),
                "total_amount": sum(inv["amount"] for inv in overdue_invoices),
                "notification_method": dunning_result.get("method"),
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar cobrança: {str(e)}")
            return {"error": str(e)}
    
    async def run_daily_dunning_process(self) -> Dict[str, Any]:
        """
        Executa processo diário de cobrança:
        1. Identifica faturas vencidas
        2. Aplica regras de cobrança
        3. Envia notificações
        4. Atualiza status
        """
        try:
            logger.info("🔄 Iniciando processo diário de cobrança")
            
            # Buscar faturas que precisam de cobrança
            invoices_to_process = await self._get_invoices_for_dunning()
            
            results = {
                "processed_invoices": 0,
                "notifications_sent": 0,
                "errors": 0,
                "details": []
            }
            
            for invoice in invoices_to_process:
                try:
                    dunning_result = await self.dunning_engine.process_invoice_dunning(invoice)
                    
                    results["processed_invoices"] += 1
                    if dunning_result.notification_sent:
                        results["notifications_sent"] += 1
                    
                    results["details"].append({
                        "invoice_id": invoice["id"],
                        "customer_id": invoice["customer_id"],
                        "action": dunning_result.action_taken,
                        "notification_sent": dunning_result.notification_sent
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar fatura {invoice.get('id')}: {str(e)}")
                    results["errors"] += 1
            
            logger.info(f"✅ Processo de cobrança concluído: {results['notifications_sent']} notificações enviadas")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro no processo diário de cobrança: {str(e)}")
            return {"error": str(e)}
    
    async def _validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validação inicial dos dados da fatura"""
        try:
            # Campos obrigatórios
            required_fields = ["id", "customer_id", "total_amount", "due_date", "items"]
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
            
            # Validar data de vencimento
            try:
                due_date = datetime.fromisoformat(invoice_data["due_date"]).date()
                if due_date <= date.today():
                    return {
                        "is_valid": False,
                        "error": "Data de vencimento deve ser futura"
                    }
            except ValueError:
                return {
                    "is_valid": False,
                    "error": "Formato de data de vencimento inválido"
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
    
    async def _send_invoice_email(self, invoice_data: Dict[str, Any], workflow: ARWorkflow) -> Dict[str, Any]:
        """Envia fatura por email para o cliente"""
        try:
            # TODO: Implementar envio real de email
            # Por enquanto, simular envio
            
            customer_email = invoice_data.get("customer_email")
            if not customer_email:
                return {"sent": False, "error": "Email do cliente não informado"}
            
            logger.info(f"📧 Simulando envio de email para {customer_email}")
            
            # Simular delay de envio
            await asyncio.sleep(0.5)
            
            return {
                "sent": True,
                "email": customer_email,
                "sent_at": datetime.utcnow().isoformat(),
                "subject": f"Fatura {invoice_data['id']} - Vencimento {invoice_data['due_date']}"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {str(e)}")
            return {"sent": False, "error": str(e)}
    
    async def _get_invoice_data(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Busca dados da fatura"""
        # TODO: Implementar busca real no banco
        return {
            "id": invoice_id,
            "customer_id": "cust-001",
            "total_amount": 1500.00,
            "due_date": "2024-02-15",
            "status": "active"
        }
    
    async def _mark_invoice_as_paid(self, invoice_id: str, payment_data: Dict[str, Any]):
        """Marca fatura como paga"""
        # TODO: Implementar atualização no banco
        logger.info(f"✅ Fatura {invoice_id} marcada como paga")
    
    async def _record_partial_payment(self, invoice_id: str, payment_data: Dict[str, Any]):
        """Registra pagamento parcial"""
        # TODO: Implementar registro no banco
        logger.info(f"💰 Pagamento parcial registrado para fatura {invoice_id}")
    
    async def _get_overdue_invoices(self, customer_id: str) -> List[Dict[str, Any]]:
        """Busca faturas em atraso de um cliente"""
        # TODO: Implementar busca real no banco
        return [
            {
                "id": "inv-001",
                "amount": 1500.00,
                "due_date": "2024-01-15",
                "days_overdue": 10
            }
        ]
    
    async def _get_invoices_for_dunning(self) -> List[Dict[str, Any]]:
        """Busca faturas que precisam de cobrança"""
        # TODO: Implementar busca real no banco
        return []
    
    async def _finalize_workflow(self, workflow: ARWorkflow) -> Dict[str, Any]:
        """Finaliza o workflow e notifica o Core API"""
        try:
            workflow.completed_at = datetime.utcnow()
            
            # Preparar resultado
            result = {
                "invoice_id": workflow.invoice_id,
                "status": workflow.status,
                "validation_result": workflow.validation_result,
                "pdf_path": workflow.pdf_path,
                "payment_methods": workflow.payment_methods,
                "email_sent": workflow.email_sent,
                "email_sent_at": workflow.email_sent_at.isoformat() if workflow.email_sent_at else None,
                "dunning_schedule": workflow.dunning_schedule,
                "due_date": workflow.due_date.isoformat() if workflow.due_date else None,
                "error_message": workflow.error_message,
                "processed_at": workflow.completed_at.isoformat(),
                "processing_time": (workflow.completed_at - workflow.created_at).total_seconds()
            }
            
            # Notificar Core API
            await self._notify_core_api(result)
            
            logger.info(f"✅ Workflow AR finalizado para fatura {workflow.invoice_id}: {workflow.status}")
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
                    f"{settings.core_api_url}/api/v1/ar/workflow-completed",
                    json=result,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Core API notificado sobre fatura {result['invoice_id']}")
                else:
                    logger.error(f"❌ Falha ao notificar Core API: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao notificar Core API: {str(e)}")
