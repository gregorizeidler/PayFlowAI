"""
Message Queue Consumer para AP Workflow Service
Consome eventos de documentos processados e executa workflow
"""

import asyncio
import json
import logging
from typing import Dict, Any
import pika
import pika.exceptions

from app.config import settings

logger = logging.getLogger(__name__)

class MessageQueueConsumer:
    """Consumer de mensagens RabbitMQ para workflow AP"""
    
    def __init__(self, workflow_engine):
        self.workflow_engine = workflow_engine
        self.connection = None
        self.channel = None
        self.consuming = False
    
    async def start_consuming(self):
        """Inicia o consumo de mensagens"""
        try:
            logger.info("🔌 Conectando ao RabbitMQ...")
            
            # Conectar ao RabbitMQ
            connection_params = pika.URLParameters(settings.rabbitmq_url)
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declarar exchanges e filas
            await self._setup_queues()
            
            # Configurar consumer
            self.channel.basic_consume(
                queue='ap_workflow_queue',
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            logger.info("✅ Consumer AP Workflow iniciado")
            self.consuming = True
            
            # Iniciar consumo em thread separada
            asyncio.create_task(self._consume_loop())
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar consumer: {str(e)}")
            raise
    
    async def _setup_queues(self):
        """Configura exchanges e filas necessárias"""
        try:
            # Exchange principal
            self.channel.exchange_declare(
                exchange='financial_automation',
                exchange_type='topic',
                durable=True
            )
            
            # Fila para workflow AP
            self.channel.queue_declare(
                queue='ap_workflow_queue',
                durable=True
            )
            
            # Bind para eventos de documentos processados
            self.channel.queue_bind(
                exchange='financial_automation',
                queue='ap_workflow_queue',
                routing_key='document.processed.invoice'
            )
            
            # Bind para eventos de faturas criadas
            self.channel.queue_bind(
                exchange='financial_automation',
                queue='ap_workflow_queue',
                routing_key='invoice.created'
            )
            
            logger.info("✅ Filas e exchanges configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar filas: {str(e)}")
            raise
    
    async def _consume_loop(self):
        """Loop principal de consumo"""
        try:
            while self.consuming and self.connection and not self.connection.is_closed:
                self.connection.process_data_events(time_limit=1)
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ Erro no loop de consumo: {str(e)}")
    
    def _on_message(self, channel, method, properties, body):
        """Callback para processar mensagens recebidas"""
        try:
            # Decodificar mensagem
            message = json.loads(body.decode('utf-8'))
            routing_key = method.routing_key
            
            logger.info(f"📨 Mensagem recebida: {routing_key}")
            
            # Processar baseado no tipo de evento
            if routing_key == 'document.processed.invoice':
                asyncio.create_task(self._handle_document_processed(message))
            elif routing_key == 'invoice.created':
                asyncio.create_task(self._handle_invoice_created(message))
            else:
                logger.warning(f"⚠️ Routing key não reconhecido: {routing_key}")
            
            # Confirmar processamento
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    async def _handle_document_processed(self, message: Dict[str, Any]):
        """Processa evento de documento processado pelo OCR/NLP"""
        try:
            document_id = message.get('document_id')
            extracted_data = message.get('extracted_data', {})
            
            logger.info(f"📄 Processando documento {document_id}")
            
            # Verificar se é uma fatura (invoice)
            document_type = extracted_data.get('document_type', '').lower()
            if document_type not in ['invoice', 'nota_fiscal', 'fatura']:
                logger.info(f"📄 Documento {document_id} não é fatura, ignorando")
                return
            
            # Converter dados extraídos para formato de fatura
            invoice_data = await self._convert_to_invoice_format(document_id, extracted_data)
            
            # Executar workflow AP
            result = await self.workflow_engine.process_invoice(invoice_data)
            
            logger.info(f"✅ Workflow concluído para documento {document_id}: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar documento: {str(e)}")
    
    async def _handle_invoice_created(self, message: Dict[str, Any]):
        """Processa evento de fatura criada manualmente"""
        try:
            invoice_data = message.get('invoice_data', {})
            invoice_id = invoice_data.get('id')
            
            logger.info(f"📝 Processando fatura criada manualmente: {invoice_id}")
            
            # Executar workflow AP
            result = await self.workflow_engine.process_invoice(invoice_data)
            
            logger.info(f"✅ Workflow concluído para fatura {invoice_id}: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar fatura criada: {str(e)}")
    
    async def _convert_to_invoice_format(self, document_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte dados extraídos do OCR para formato de fatura"""
        try:
            # Mapear campos do OCR para formato padrão
            invoice_data = {
                "id": f"inv-{document_id}",
                "document_id": document_id,
                "supplier_id": extracted_data.get('supplier_cnpj') or extracted_data.get('supplier_id'),
                "supplier_name": extracted_data.get('supplier_name'),
                "invoice_number": extracted_data.get('invoice_number'),
                "total_amount": float(extracted_data.get('total_amount', 0)),
                "invoice_date": extracted_data.get('invoice_date'),
                "due_date": extracted_data.get('due_date'),
                "items": extracted_data.get('items', []),
                "tax_amount": float(extracted_data.get('tax_amount', 0)),
                "currency": extracted_data.get('currency', 'BRL'),
                "payment_terms": extracted_data.get('payment_terms'),
                "created_from_ocr": True,
                "ocr_confidence": extracted_data.get('confidence_score', 0)
            }
            
            # Validar campos obrigatórios
            if not invoice_data['supplier_id']:
                raise ValueError("CNPJ do fornecedor não encontrado")
            
            if invoice_data['total_amount'] <= 0:
                raise ValueError("Valor total inválido")
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao converter dados do OCR: {str(e)}")
            raise
    
    async def stop_consuming(self):
        """Para o consumo de mensagens"""
        try:
            logger.info("🛑 Parando consumer...")
            self.consuming = False
            
            if self.channel and not self.channel.is_closed:
                self.channel.stop_consuming()
                self.channel.close()
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            logger.info("✅ Consumer parado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar consumer: {str(e)}")
    
    def publish_workflow_result(self, result: Dict[str, Any]):
        """Publica resultado do workflow para outros serviços"""
        try:
            if not self.channel or self.channel.is_closed:
                logger.warning("⚠️ Canal não disponível para publicação")
                return
            
            routing_key = f"ap.workflow.{result.get('status', 'completed')}"
            
            self.channel.basic_publish(
                exchange='financial_automation',
                routing_key=routing_key,
                body=json.dumps(result),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistir mensagem
                    content_type='application/json'
                )
            )
            
            logger.info(f"📤 Resultado do workflow publicado: {routing_key}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar resultado: {str(e)}")
