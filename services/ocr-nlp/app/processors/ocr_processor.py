"""
Processador OCR usando Tesseract
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
import pdf2image
import os
import time
import logging
from typing import Dict, Any, Optional
import tempfile

from app.config import settings

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Processador OCR com Tesseract"""
    
    def __init__(self):
        # Configurar Tesseract
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        
    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extrai texto de um arquivo usando OCR
        Suporta: PDF, PNG, JPG, JPEG
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Iniciando OCR para arquivo: {file_path}")
            
            # Determinar tipo do arquivo
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                text, confidence = await self._process_pdf(file_path)
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                text, confidence = await self._process_image(file_path)
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_extension}")
            
            processing_time = time.time() - start_time
            
            result = {
                "text": text,
                "confidence": confidence,
                "processing_time": round(processing_time, 2),
                "file_type": file_extension,
                "status": "success"
            }
            
            logger.info(f"✅ OCR concluído. Confiança: {confidence}%, Tempo: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no OCR: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": time.time() - start_time,
                "status": "error",
                "error": str(e)
            }
    
    async def _process_pdf(self, pdf_path: str) -> tuple[str, float]:
        """Processa arquivo PDF convertendo para imagens"""
        try:
            # Converter PDF para imagens
            pages = pdf2image.convert_from_path(
                pdf_path,
                dpi=settings.pdf_dpi,
                first_page=1,
                last_page=5  # Limitar a 5 páginas para performance
            )
            
            all_text = []
            confidences = []
            
            for i, page in enumerate(pages):
                logger.info(f"📄 Processando página {i+1}/{len(pages)}")
                
                # Pré-processar imagem
                processed_image = self._preprocess_image(np.array(page))
                
                # Executar OCR
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=settings.ocr_languages,
                    config=settings.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extrair texto e confiança
                page_text = []
                page_confidences = []
                
                for j in range(len(data['text'])):
                    if int(data['conf'][j]) > 0:  # Filtrar palavras com confiança > 0
                        page_text.append(data['text'][j])
                        page_confidences.append(int(data['conf'][j]))
                
                if page_text:
                    all_text.append(' '.join(page_text))
                    confidences.extend(page_confidences)
            
            # Combinar texto de todas as páginas
            full_text = '\n\n'.join(all_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, round(avg_confidence, 2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar PDF: {str(e)}")
            raise
    
    async def _process_image(self, image_path: str) -> tuple[str, float]:
        """Processa arquivo de imagem"""
        try:
            # Carregar imagem
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Não foi possível carregar a imagem")
            
            # Pré-processar imagem
            processed_image = self._preprocess_image(image)
            
            # Executar OCR
            data = pytesseract.image_to_data(
                processed_image,
                lang=settings.ocr_languages,
                config=settings.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extrair texto e confiança
            text_parts = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    text_parts.append(data['text'][i])
                    confidences.append(int(data['conf'][i]))
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, round(avg_confidence, 2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar imagem: {str(e)}")
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Pré-processa imagem para melhorar OCR:
        - Redimensiona se muito grande
        - Converte para escala de cinza
        - Aplica filtros para melhorar qualidade
        - Corrige inclinação
        """
        try:
            # Redimensionar se muito grande
            height, width = image.shape[:2]
            if max(height, width) > settings.max_image_size:
                scale = settings.max_image_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Converter para escala de cinza
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Aplicar filtro de desfoque gaussiano para reduzir ruído
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Aplicar threshold adaptativo para binarização
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Aplicar operações morfológicas para limpar a imagem
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Erro no pré-processamento: {str(e)}")
            # Retornar imagem original em caso de erro
            return image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
