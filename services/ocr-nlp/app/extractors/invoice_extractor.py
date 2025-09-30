"""
Extrator de dados de notas fiscais e faturas
"""

import re
import spacy
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class InvoiceExtractor:
    """Extrator especializado em notas fiscais brasileiras"""
    
    def __init__(self):
        try:
            # Carregar modelo spaCy português
            self.nlp = spacy.load("pt_core_news_sm")
            logger.info("✅ Modelo spaCy português carregado")
        except OSError:
            logger.error("❌ Modelo spaCy português não encontrado")
            self.nlp = None
    
    async def extract(self, text: str, file_path: str = None) -> Dict[str, Any]:
        """
        Extrai dados estruturados de nota fiscal
        """
        try:
            logger.info("🧠 Iniciando extração de dados da nota fiscal")
            
            # Limpar e normalizar texto
            cleaned_text = self._clean_text(text)
            
            # Extrair informações básicas
            invoice_data = {
                "type": "invoice",
                "confidence": 0.0,
                "extracted_fields": {}
            }
            
            # 1. Número da nota fiscal
            invoice_number = self._extract_invoice_number(cleaned_text)
            if invoice_number:
                invoice_data["extracted_fields"]["invoice_number"] = invoice_number
                invoice_data["confidence"] += 15
            
            # 2. CNPJ do emitente
            cnpj = self._extract_cnpj(cleaned_text)
            if cnpj:
                invoice_data["extracted_fields"]["cnpj"] = cnpj
                invoice_data["confidence"] += 20
            
            # 3. Data de emissão
            issue_date = self._extract_date(cleaned_text, "emissao|emissão")
            if issue_date:
                invoice_data["extracted_fields"]["issue_date"] = issue_date
                invoice_data["confidence"] += 15
            
            # 4. Data de vencimento
            due_date = self._extract_date(cleaned_text, "vencimento")
            if due_date:
                invoice_data["extracted_fields"]["due_date"] = due_date
                invoice_data["confidence"] += 10
            
            # 5. Valor total
            total_amount = self._extract_amount(cleaned_text)
            if total_amount:
                invoice_data["extracted_fields"]["total_amount"] = total_amount
                invoice_data["confidence"] += 20
            
            # 6. Nome do fornecedor/emitente
            supplier_name = self._extract_supplier_name(cleaned_text)
            if supplier_name:
                invoice_data["extracted_fields"]["supplier_name"] = supplier_name
                invoice_data["confidence"] += 10
            
            # 7. Linha digitável (se for boleto)
            digitable_line = self._extract_digitable_line(cleaned_text)
            if digitable_line:
                invoice_data["extracted_fields"]["digitable_line"] = digitable_line
                invoice_data["confidence"] += 10
            
            # 8. Código de barras
            barcode = self._extract_barcode(cleaned_text)
            if barcode:
                invoice_data["extracted_fields"]["barcode"] = barcode
                invoice_data["confidence"] += 5
            
            # 9. Itens da nota (usando NLP)
            if self.nlp:
                items = self._extract_items_with_nlp(cleaned_text)
                if items:
                    invoice_data["extracted_fields"]["items"] = items
                    invoice_data["confidence"] += 5
            
            logger.info(f"✅ Extração concluída. Confiança: {invoice_data['confidence']}%")
            return invoice_data
            
        except Exception as e:
            logger.error(f"❌ Erro na extração: {str(e)}")
            return {
                "type": "invoice",
                "confidence": 0.0,
                "error": str(e),
                "extracted_fields": {}
            }
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto"""
        # Remover caracteres especiais desnecessários
        text = re.sub(r'[^\w\s\.,\-\/\(\):]', ' ', text)
        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extrai número da nota fiscal"""
        patterns = [
            r'(?:nota\s*fiscal|nf|n[°º])\s*:?\s*(\d+)',
            r'número\s*:?\s*(\d+)',
            r'nº\s*(\d+)',
            r'(\d{6,})'  # Sequência de 6+ dígitos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_cnpj(self, text: str) -> Optional[str]:
        """Extrai CNPJ do texto"""
        # Padrão CNPJ: XX.XXX.XXX/XXXX-XX
        pattern = r'\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2}'
        match = re.search(pattern, text)
        if match:
            cnpj = re.sub(r'[^\d]', '', match.group())
            if len(cnpj) == 14:
                return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return None
    
    def _extract_date(self, text: str, context: str) -> Optional[str]:
        """Extrai data baseada no contexto"""
        # Procurar por contexto + data
        pattern = f"{context}.*?(\\d{{1,2}}[\/\\-]\\d{{1,2}}[\/\\-]\\d{{2,4}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                # Tentar diferentes formatos
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                pass
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extrai valor total da nota"""
        patterns = [
            r'(?:total|valor|r\$)\s*:?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(?:total|valor)\s*:?\s*(\d+,\d{2})',
            r'r\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Converter formato brasileiro para float
                    amount_str = match.replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    if 10 <= amount <= 1000000:  # Filtro de valores razoáveis
                        amounts.append(amount)
                except ValueError:
                    continue
        
        # Retornar o maior valor encontrado (provavelmente o total)
        return max(amounts) if amounts else None
    
    def _extract_supplier_name(self, text: str) -> Optional[str]:
        """Extrai nome do fornecedor"""
        # Procurar por padrões comuns de nome de empresa
        patterns = [
            r'(?:razão\s*social|empresa|fornecedor)\s*:?\s*([A-Z][A-Za-z\s]+(?:LTDA|S\.A\.|ME|EPP)?)',
            r'([A-Z][A-Za-z\s]+(?:LTDA|S\.A\.|ME|EPP))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 5:  # Nome mínimo
                    return name
        return None
    
    def _extract_digitable_line(self, text: str) -> Optional[str]:
        """Extrai linha digitável do boleto"""
        # Padrão linha digitável: 5 grupos de números
        pattern = r'(\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        
        # Padrão alternativo sem formatação
        pattern = r'(\d{47,48})'
        match = re.search(pattern, text)
        if match:
            line = match.group(1)
            # Formatar linha digitável
            if len(line) == 47:
                return f"{line[:5]}.{line[5:10]} {line[10:15]}.{line[15:21]} {line[21:26]}.{line[26:32]} {line[32]} {line[33:]}"
        
        return None
    
    def _extract_barcode(self, text: str) -> Optional[str]:
        """Extrai código de barras"""
        # Código de barras geralmente tem 44 dígitos
        pattern = r'(\d{44})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return None
    
    def _extract_items_with_nlp(self, text: str) -> List[Dict[str, Any]]:
        """Extrai itens da nota usando NLP"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            items = []
            
            # Procurar por padrões de itens
            # Isso é uma implementação básica - pode ser muito mais sofisticada
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(word in sent_text for word in ['produto', 'serviço', 'item', 'descrição']):
                    # Tentar extrair quantidade e valor
                    quantity_match = re.search(r'(\d+(?:,\d+)?)\s*(?:un|und|unid)', sent_text)
                    value_match = re.search(r'(\d+,\d{2})', sent_text)
                    
                    if quantity_match or value_match:
                        item = {
                            "description": sent.text.strip()[:100],
                            "quantity": float(quantity_match.group(1).replace(',', '.')) if quantity_match else 1.0,
                            "unit_price": float(value_match.group(1).replace(',', '.')) if value_match else 0.0
                        }
                        items.append(item)
            
            return items[:10]  # Limitar a 10 itens
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de itens com NLP: {str(e)}")
            return []
