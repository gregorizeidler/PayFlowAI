"""
Processador principal de documentos
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from app.processors.ocr_processor import OCRProcessor
from app.extractors.invoice_extractor import InvoiceExtractor
from app.extractors.bank_statement_extractor import BankStatementExtractor
from app.utils.storage_client import StorageClient
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processador principal de documentos"""
    
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.invoice_extractor = InvoiceExtractor()
        self.bank_extractor = BankStatementExtractor()
        self.storage_client = StorageClient()
        
    async def process_document(self, document_id: str, file_path: str) -> Dict[str, Any]:
        """
        Processa um documento completo:
        1. Download do arquivo
        2. OCR para extrair texto
        3. NLP para extrair dados estruturados
        4. Retorna dados extraídos
        """
        try:
            logger.info(f"🔄 Iniciando processamento do documento {document_id}")
            
            # 1. Download do arquivo do MinIO
            local_file_path = await self.storage_client.download_file(file_path)
            if not local_file_path:
                raise Exception("Falha ao baixar arquivo do storage")
            
            # 2. Determinar tipo do documento
            document_type = self._detect_document_type(file_path)
            
            # 3. Executar OCR
            logger.info(f"📖 Executando OCR no documento {document_id}")
            ocr_result = await self.ocr_processor.extract_text(local_file_path)
            
            if ocr_result["confidence"] < settings.min_ocr_confidence:
                logger.warning(f"⚠️ Baixa confiança no OCR: {ocr_result['confidence']}%")
            
            # 4. Extrair dados estruturados baseado no tipo
            logger.info(f"🧠 Extraindo dados estruturados do documento {document_id}")
            extracted_data = await self._extract_structured_data(
                document_type, 
                ocr_result["text"],
                local_file_path
            )
            
            # 5. Compilar resultado final
            result = {
                "document_id": document_id,
                "document_type": document_type,
                "processing_status": "completed",
                "ocr_confidence": ocr_result["confidence"],
                "extracted_text": ocr_result["text"],
                "extracted_data": extracted_data,
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time": ocr_result.get("processing_time", 0)
            }
            
            # 6. Notificar Core API
            await self._notify_core_api(document_id, result)
            
            # 7. Cleanup
            await self.storage_client.cleanup_temp_file(local_file_path)
            
            logger.info(f"✅ Documento {document_id} processado com sucesso")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar documento {document_id}: {str(e)}")
            
            # Notificar erro
            error_result = {
                "document_id": document_id,
                "processing_status": "failed",
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            await self._notify_core_api(document_id, error_result)
            return error_result
    
    def _detect_document_type(self, file_path: str) -> str:
        """Detecta o tipo do documento baseado no nome do arquivo"""
        file_path_lower = file_path.lower()
        
        if any(keyword in file_path_lower for keyword in ["nf", "nota", "fiscal", "invoice"]):
            return "invoice"
        elif any(keyword in file_path_lower for keyword in ["boleto", "cobranca", "bill"]):
            return "bill"
        elif any(keyword in file_path_lower for keyword in ["extrato", "statement", "bank"]):
            return "bank_statement"
        elif any(keyword in file_path_lower for keyword in ["recibo", "receipt"]):
            return "receipt"
        else:
            return "unknown"
    
    async def _extract_structured_data(
        self, 
        document_type: str, 
        text: str, 
        file_path: str
    ) -> Dict[str, Any]:
        """Extrai dados estruturados baseado no tipo do documento"""
        
        if document_type == "invoice":
            return await self.invoice_extractor.extract(text, file_path)
        elif document_type == "bank_statement":
            return await self.bank_extractor.extract(text, file_path)
        elif document_type in ["bill", "receipt"]:
            # Usar extrator de invoice para boletos e recibos
            return await self.invoice_extractor.extract(text, file_path)
        else:
            # Extração genérica
            return {
                "type": "generic",
                "confidence": 50.0,
                "raw_text": text[:500] + "..." if len(text) > 500 else text
            }
    
    async def _notify_core_api(self, document_id: str, result: Dict[str, Any]):
        """Notifica o Core API sobre o resultado do processamento"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.core_api_url}/api/v1/documents/{document_id}/processed",
                    json=result,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Core API notificado sobre documento {document_id}")
                else:
                    logger.error(f"❌ Falha ao notificar Core API: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao notificar Core API: {str(e)}")
