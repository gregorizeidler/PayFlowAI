"""
Consumer de mensagens RabbitMQ para processamento de documentos
"""

import pika
import json
import asyncio
import logging
from typing import Dict, Any
import threading

from app.config import settings

logger = logging.getLogger(__name__)

class MessageQueueConsumer:
    """Consumer para processar mensagens de documentos recebidos"""
    
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.connection = None
        self.channel = None
        self.consuming = False
        
    async def start_consuming(self):
        """Inicia o consumo de mensagens"""
        try:
            logger.info("🐰 Conectando ao RabbitMQ...")
            
            # Conectar ao RabbitMQ
            parameters = pika.URLParameters(settings.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar fila de documentos recebidos
            self.channel.queue_declare(queue='document.received', durable=True)
            
            # Configurar QoS para processar uma mensagem por vez
            self.channel.basic_qos(prefetch_count=1)
            
            # Configurar callback
            self.channel.basic_consume(
                queue='document.received',
                on_message_callback=self._process_message,
                auto_ack=False
            )
            
            self.consuming = True
            logger.info("✅ Iniciando consumo de mensagens...")
            
            # Iniciar consumo em thread separada
            consume_thread = threading.Thread(target=self._start_consuming_thread)
            consume_thread.daemon = True
            consume_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar consumer: {e}")
            raise
    
    def _start_consuming_thread(self):
        """Thread para consumir mensagens"""
        try:
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"❌ Erro no thread de consumo: {e}")
    
    def _process_message(self, channel, method, properties, body):
        """Processa mensagem recebida"""
        try:
            # Parse da mensagem
            message = json.loads(body.decode('utf-8'))
            logger.info(f"📨 Mensagem recebida: {message.get('event_type')}")
            
            if message.get('event_type') == 'document_received':
                # Processar documento em background
                document_id = message.get('document_id')
                file_path = message.get('file_path')
                
                if document_id and file_path:
                    # Executar processamento
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            self.document_processor.process_document(document_id, file_path)
                        )
                        logger.info(f"✅ Documento {document_id} processado com sucesso")
                        
                        # Acknowledge da mensagem
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar documento {document_id}: {e}")
                        # Rejeitar mensagem (vai para DLQ se configurado)
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
                    finally:
                        loop.close()
                else:
                    logger.error("❌ Mensagem inválida: faltam document_id ou file_path")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                logger.warning(f"⚠️ Tipo de evento não reconhecido: {message.get('event_type')}")
                channel.basic_ack(delivery_tag=method.delivery_tag)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar mensagem JSON: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao processar mensagem: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    async def stop_consuming(self):
        """Para o consumo de mensagens"""
        try:
            if self.consuming and self.channel:
                self.channel.stop_consuming()
                self.consuming = False
                logger.info("🛑 Consumo de mensagens parado")
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("🛑 Conexão RabbitMQ fechada")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar consumer: {e}")
    
    def publish_processed_document(self, document_id: str, result: Dict[str, Any]):
        """Publica resultado do processamento"""
        try:
            if not self.channel:
                logger.error("❌ Canal RabbitMQ não disponível")
                return
            
            # Declarar fila de documentos processados
            self.channel.queue_declare(queue='document.processed', durable=True)
            
            message = {
                "event_type": "document_processed",
                "document_id": document_id,
                "result": result,
                "timestamp": "now"
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='document.processed',
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(delivery_mode=2)  # Persistir mensagem
            )
            
            logger.info(f"📤 Resultado publicado para documento {document_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar resultado: {e}")
