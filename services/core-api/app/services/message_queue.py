"""
Serviço de Message Queue usando RabbitMQ
"""

import pika
import json
import asyncio
from typing import Dict, Any, Callable, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MessageQueueService:
    """Serviço para gerenciar filas de mensagens"""
    
    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        
        # Definir filas do sistema
        self.queues = {
            "document.received": {
                "routing_key": "document.received",
                "exchange": "financial_automation",
                "durable": True
            },
            "document.processed": {
                "routing_key": "document.processed", 
                "exchange": "financial_automation",
                "durable": True
            },
            "ap.created": {
                "routing_key": "ap.created",
                "exchange": "financial_automation", 
                "durable": True
            },
            "ap.approved": {
                "routing_key": "ap.approved",
                "exchange": "financial_automation",
                "durable": True
            },
            "ar.created": {
                "routing_key": "ar.created",
                "exchange": "financial_automation",
                "durable": True
            },
            "payment.scheduled": {
                "routing_key": "payment.scheduled",
                "exchange": "financial_automation",
                "durable": True
            },
            "reconciliation.required": {
                "routing_key": "reconciliation.required",
                "exchange": "financial_automation",
                "durable": True
            }
        }
    
    async def connect(self):
        """Conectar ao RabbitMQ"""
        try:
            # Parse da URL do RabbitMQ
            parameters = pika.URLParameters(settings.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar exchange principal
            self.channel.exchange_declare(
                exchange="financial_automation",
                exchange_type="topic",
                durable=True
            )
            
            # Declarar todas as filas
            for queue_name, config in self.queues.items():
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=config["durable"]
                )
                
                # Bind da fila ao exchange
                self.channel.queue_bind(
                    exchange=config["exchange"],
                    queue=queue_name,
                    routing_key=config["routing_key"]
                )
            
            logger.info("✅ Conectado ao RabbitMQ com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar do RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("✅ Desconectado do RabbitMQ")
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar do RabbitMQ: {e}")
    
    def publish_message(self, routing_key: str, message: Dict[str, Any]):
        """Publicar mensagem na fila"""
        try:
            if not self.channel:
                raise Exception("Canal não está conectado")
            
            # Serializar mensagem
            message_body = json.dumps(message, default=str)
            
            # Publicar mensagem
            self.channel.basic_publish(
                exchange="financial_automation",
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Tornar mensagem persistente
                    content_type="application/json"
                )
            )
            
            logger.info(f"📤 Mensagem publicada: {routing_key}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar mensagem: {e}")
            raise
    
    def publish_document_received(self, document_id: str, company_id: str, file_path: str):
        """Publicar evento de documento recebido"""
        message = {
            "event_type": "document_received",
            "document_id": document_id,
            "company_id": company_id,
            "file_path": file_path,
            "timestamp": "now"
        }
        self.publish_message("document.received", message)
    
    def publish_document_processed(self, document_id: str, extracted_data: Dict[str, Any]):
        """Publicar evento de documento processado"""
        message = {
            "event_type": "document_processed",
            "document_id": document_id,
            "extracted_data": extracted_data,
            "timestamp": "now"
        }
        self.publish_message("document.processed", message)
    
    def publish_ap_created(self, ap_id: str, company_id: str, supplier_id: str, amount: float):
        """Publicar evento de conta a pagar criada"""
        message = {
            "event_type": "ap_created",
            "ap_id": ap_id,
            "company_id": company_id,
            "supplier_id": supplier_id,
            "amount": amount,
            "timestamp": "now"
        }
        self.publish_message("ap.created", message)
    
    def publish_ap_approved(self, ap_id: str, approved_by: str):
        """Publicar evento de conta a pagar aprovada"""
        message = {
            "event_type": "ap_approved",
            "ap_id": ap_id,
            "approved_by": approved_by,
            "timestamp": "now"
        }
        self.publish_message("ap.approved", message)
    
    def publish_ar_created(self, ar_id: str, company_id: str, customer_id: str, amount: float):
        """Publicar evento de conta a receber criada"""
        message = {
            "event_type": "ar_created",
            "ar_id": ar_id,
            "company_id": company_id,
            "customer_id": customer_id,
            "amount": amount,
            "timestamp": "now"
        }
        self.publish_message("ar.created", message)
    
    def publish_payment_scheduled(self, ap_id: str, payment_date: str, amount: float):
        """Publicar evento de pagamento agendado"""
        message = {
            "event_type": "payment_scheduled",
            "ap_id": ap_id,
            "payment_date": payment_date,
            "amount": amount,
            "timestamp": "now"
        }
        self.publish_message("payment.scheduled", message)
    
    def publish_reconciliation_required(self, company_id: str, transaction_data: Dict[str, Any]):
        """Publicar evento de conciliação necessária"""
        message = {
            "event_type": "reconciliation_required",
            "company_id": company_id,
            "transaction_data": transaction_data,
            "timestamp": "now"
        }
        self.publish_message("reconciliation.required", message)
