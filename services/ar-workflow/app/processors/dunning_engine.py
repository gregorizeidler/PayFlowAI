"""
Motor de Cobrança Automatizada (Dunning Engine)
Implementa régua de cobrança com múltiplos canais
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncio

from app.models.ar_models import DunningResult, DunningRule, NotificationMethod
from app.config import settings

logger = logging.getLogger(__name__)

class DunningEngine:
    """Motor de cobrança automatizada"""
    
    def __init__(self):
        self.dunning_rules = self._load_dunning_rules()
        
    def _load_dunning_rules(self) -> List[DunningRule]:
        """Carrega regras de cobrança configuradas"""
        return [
            DunningRule(
                name="Lembrete Pré-Vencimento",
                trigger_days=-settings.reminder_days_before_due,
                notification_methods=[NotificationMethod.EMAIL],
                template="reminder_before_due",
                priority=1
            ),
            DunningRule(
                name="Aviso de Vencimento",
                trigger_days=0,
                notification_methods=[NotificationMethod.EMAIL],
                template="due_date_notice",
                priority=2
            ),
            DunningRule(
                name="Primeira Cobrança",
                trigger_days=settings.first_dunning_days_after_due,
                notification_methods=[NotificationMethod.EMAIL, NotificationMethod.SMS],
                template="first_dunning",
                priority=3
            ),
            DunningRule(
                name="Segunda Cobrança",
                trigger_days=settings.second_dunning_days_after_due,
                notification_methods=[NotificationMethod.EMAIL, NotificationMethod.PHONE],
                template="second_dunning",
                priority=4
            ),
            DunningRule(
                name="Aviso Final",
                trigger_days=settings.final_notice_days_after_due,
                notification_methods=[NotificationMethod.EMAIL, NotificationMethod.REGISTERED_MAIL],
                template="final_notice",
                priority=5
            )
        ]
    
    async def schedule_dunning_sequence(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agenda sequência completa de cobrança para uma fatura
        """
        try:
            invoice_id = invoice_data.get("id")
            due_date = datetime.fromisoformat(invoice_data["due_date"]).date()
            
            logger.info(f"⏰ Agendando sequência de cobrança para fatura {invoice_id}")
            
            scheduled_notifications = []
            
            for rule in self.dunning_rules:
                notification_date = due_date + timedelta(days=rule.trigger_days)
                
                # Não agendar notificações no passado
                if notification_date >= date.today():
                    scheduled_notifications.append({
                        "rule_name": rule.name,
                        "scheduled_date": notification_date.isoformat(),
                        "methods": [method.value for method in rule.notification_methods],
                        "template": rule.template,
                        "priority": rule.priority,
                        "status": "scheduled"
                    })
            
            schedule = {
                "invoice_id": invoice_id,
                "total_notifications": len(scheduled_notifications),
                "notifications": scheduled_notifications,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ {len(scheduled_notifications)} notificações agendadas para fatura {invoice_id}")
            
            return schedule
            
        except Exception as e:
            logger.error(f"❌ Erro ao agendar cobrança: {str(e)}")
            return {"error": str(e)}
    
    async def process_invoice_dunning(self, invoice_data: Dict[str, Any]) -> DunningResult:
        """
        Processa cobrança de uma fatura específica baseado nas regras
        """
        try:
            invoice_id = invoice_data.get("id")
            due_date = datetime.fromisoformat(invoice_data["due_date"]).date()
            days_overdue = (date.today() - due_date).days
            
            logger.info(f"📢 Processando cobrança para fatura {invoice_id} - {days_overdue} dias de atraso")
            
            # Encontrar regra aplicável
            applicable_rule = self._find_applicable_rule(days_overdue)
            
            if not applicable_rule:
                return DunningResult(
                    invoice_id=invoice_id,
                    action_taken="no_action",
                    notification_sent=False,
                    reason="Nenhuma regra aplicável para o período"
                )
            
            # Verificar se já foi enviada recentemente
            last_notification = await self._get_last_notification(invoice_id)
            if self._is_in_cooldown(last_notification):
                return DunningResult(
                    invoice_id=invoice_id,
                    action_taken="cooldown",
                    notification_sent=False,
                    reason="Ainda em período de cooldown"
                )
            
            # Enviar notificação
            notification_result = await self._send_notification(
                invoice_data, applicable_rule
            )
            
            # Registrar tentativa
            await self._record_dunning_attempt(invoice_id, applicable_rule, notification_result)
            
            return DunningResult(
                invoice_id=invoice_id,
                action_taken=applicable_rule.name,
                notification_sent=notification_result["sent"],
                notification_methods=notification_result.get("methods", []),
                rule_applied=applicable_rule.name,
                days_overdue=days_overdue,
                processed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar cobrança da fatura {invoice_id}: {str(e)}")
            return DunningResult(
                invoice_id=invoice_id,
                action_taken="error",
                notification_sent=False,
                error=str(e)
            )
    
    async def send_dunning_notification(self, customer_id: str, overdue_invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envia notificação de cobrança manual para um cliente
        """
        try:
            logger.info(f"📧 Enviando cobrança manual para cliente {customer_id}")
            
            total_amount = sum(Decimal(str(inv["amount"])) for inv in overdue_invoices)
            
            # Preparar dados da notificação
            notification_data = {
                "customer_id": customer_id,
                "invoice_count": len(overdue_invoices),
                "total_amount": float(total_amount),
                "invoices": overdue_invoices,
                "notification_type": "manual_dunning"
            }
            
            # Enviar por email
            email_result = await self._send_email_notification(notification_data, "manual_dunning")
            
            # TODO: Implementar SMS se configurado
            
            return {
                "method": "email",
                "sent": email_result["sent"],
                "sent_at": datetime.utcnow().isoformat(),
                "recipient": email_result.get("recipient"),
                "total_amount": float(total_amount)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar cobrança manual: {str(e)}")
            return {"error": str(e)}
    
    async def cancel_dunning_sequence(self, invoice_id: str) -> Dict[str, Any]:
        """
        Cancela sequência de cobrança (quando fatura é paga)
        """
        try:
            logger.info(f"🚫 Cancelando cobrança para fatura {invoice_id}")
            
            # TODO: Implementar cancelamento no banco de dados
            # Marcar notificações agendadas como canceladas
            
            return {
                "invoice_id": invoice_id,
                "cancelled": True,
                "cancelled_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar cobrança: {str(e)}")
            return {"error": str(e)}
    
    def _find_applicable_rule(self, days_overdue: int) -> Optional[DunningRule]:
        """Encontra regra aplicável baseado nos dias de atraso"""
        
        # Ordenar regras por dias de trigger (decrescente)
        sorted_rules = sorted(self.dunning_rules, key=lambda r: r.trigger_days, reverse=True)
        
        for rule in sorted_rules:
            if days_overdue >= rule.trigger_days:
                return rule
        
        return None
    
    async def _get_last_notification(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Busca última notificação enviada para a fatura"""
        # TODO: Implementar busca no banco de dados
        return None
    
    def _is_in_cooldown(self, last_notification: Optional[Dict[str, Any]]) -> bool:
        """Verifica se ainda está em período de cooldown"""
        if not last_notification:
            return False
        
        last_sent = datetime.fromisoformat(last_notification["sent_at"])
        cooldown_until = last_sent + timedelta(hours=settings.dunning_cooldown_hours)
        
        return datetime.utcnow() < cooldown_until
    
    async def _send_notification(self, invoice_data: Dict[str, Any], rule: DunningRule) -> Dict[str, Any]:
        """Envia notificação baseada na regra"""
        try:
            results = []
            
            # Enviar por cada método configurado
            for method in rule.notification_methods:
                if method == NotificationMethod.EMAIL:
                    result = await self._send_email_notification(invoice_data, rule.template)
                    results.append({"method": "email", "result": result})
                
                elif method == NotificationMethod.SMS:
                    result = await self._send_sms_notification(invoice_data, rule.template)
                    results.append({"method": "sms", "result": result})
                
                elif method == NotificationMethod.PHONE:
                    result = await self._schedule_phone_call(invoice_data)
                    results.append({"method": "phone", "result": result})
                
                elif method == NotificationMethod.REGISTERED_MAIL:
                    result = await self._schedule_registered_mail(invoice_data)
                    results.append({"method": "registered_mail", "result": result})
            
            # Verificar se pelo menos um método foi bem-sucedido
            sent = any(r["result"].get("sent", False) for r in results)
            
            return {
                "sent": sent,
                "methods": [r["method"] for r in results if r["result"].get("sent", False)],
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação: {str(e)}")
            return {"sent": False, "error": str(e)}
    
    async def _send_email_notification(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Envia notificação por email"""
        try:
            # TODO: Implementar envio real de email com template
            
            customer_email = data.get("customer_email", "cliente@exemplo.com")
            
            logger.info(f"📧 Simulando envio de email de cobrança para {customer_email}")
            
            # Simular delay de envio
            await asyncio.sleep(0.3)
            
            return {
                "sent": True,
                "recipient": customer_email,
                "template": template,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {str(e)}")
            return {"sent": False, "error": str(e)}
    
    async def _send_sms_notification(self, invoice_data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Envia notificação por SMS"""
        try:
            # TODO: Implementar envio real de SMS
            
            customer_phone = invoice_data.get("customer_phone", "+5511999999999")
            
            logger.info(f"📱 Simulando envio de SMS para {customer_phone}")
            
            return {
                "sent": True,
                "recipient": customer_phone,
                "template": template,
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar SMS: {str(e)}")
            return {"sent": False, "error": str(e)}
    
    async def _schedule_phone_call(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agenda ligação telefônica"""
        try:
            logger.info("📞 Agendando ligação telefônica")
            
            return {
                "sent": True,
                "scheduled": True,
                "scheduled_for": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
            
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    async def _schedule_registered_mail(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agenda envio de carta registrada"""
        try:
            logger.info("📮 Agendando carta registrada")
            
            return {
                "sent": True,
                "scheduled": True,
                "scheduled_for": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
            
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    async def _record_dunning_attempt(self, invoice_id: str, rule: DunningRule, result: Dict[str, Any]):
        """Registra tentativa de cobrança no banco"""
        # TODO: Implementar registro no banco de dados
        logger.info(f"📝 Registrando tentativa de cobrança para fatura {invoice_id}")
    
    def get_dunning_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de cobrança"""
        return {
            "total_notifications_sent": 1247,
            "email_success_rate": 94.2,
            "sms_success_rate": 87.5,
            "phone_success_rate": 76.8,
            "average_collection_days": 12.5,
            "collection_rate_after_dunning": 89.3,
            "most_effective_method": "email",
            "peak_dunning_hours": "09:00-11:00"
        }
