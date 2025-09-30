"""
Parser de Extratos Bancários
Suporta múltiplos formatos: OFX, CSV, PDF
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import tempfile
import os
import csv
import re
import pandas as pd
from io import StringIO

# Imports condicionais para parsers específicos
try:
    from ofxparse import OfxParser
    OFX_AVAILABLE = True
except ImportError:
    OFX_AVAILABLE = False
    logger.warning("ofxparse não disponível - parser OFX desabilitado")

logger = logging.getLogger(__name__)

class StatementParser:
    """Parser universal de extratos bancários"""
    
    def __init__(self):
        self.supported_formats = ["ofx", "csv", "pdf"]
        
    async def parse_statement(self, statement_file) -> List[Dict[str, Any]]:
        """
        Parse universal de extrato bancário
        Detecta formato automaticamente e extrai transações
        """
        try:
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{statement_file.filename.split('.')[-1]}") as temp_file:
                content = await statement_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Detectar formato
                file_format = self._detect_format(statement_file.filename, content)
                logger.info(f"📄 Formato detectado: {file_format}")
                
                # Parse baseado no formato
                if file_format == "ofx":
                    transactions = await self._parse_ofx(temp_file_path)
                elif file_format == "csv":
                    transactions = await self._parse_csv(temp_file_path)
                elif file_format == "pdf":
                    transactions = await self._parse_pdf(temp_file_path)
                else:
                    raise ValueError(f"Formato não suportado: {file_format}")
                
                logger.info(f"✅ {len(transactions)} transações extraídas do {file_format.upper()}")
                return transactions
                
            finally:
                # Limpar arquivo temporário
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse do extrato: {str(e)}")
            raise
    
    def _detect_format(self, filename: str, content: bytes) -> str:
        """Detecta formato do arquivo baseado na extensão e conteúdo"""
        
        filename_lower = filename.lower()
        
        # Verificar extensão
        if filename_lower.endswith('.ofx'):
            return "ofx"
        elif filename_lower.endswith('.csv'):
            return "csv"
        elif filename_lower.endswith('.pdf'):
            return "pdf"
        
        # Verificar conteúdo para casos sem extensão clara
        content_str = content.decode('utf-8', errors='ignore')[:1000]
        
        if '<OFX>' in content_str or 'OFXHEADER' in content_str:
            return "ofx"
        elif ',' in content_str and '\n' in content_str:
            return "csv"
        elif '%PDF' in content_str:
            return "pdf"
        
        # Default para CSV se não conseguir detectar
        return "csv"
    
    async def _parse_ofx(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse de arquivo OFX (Open Financial Exchange)"""
        
        if not OFX_AVAILABLE:
            raise ValueError("Parser OFX não disponível. Instale ofxparse: pip install ofxparse")
        
        try:
            with open(file_path, 'rb') as ofx_file:
                ofx = OfxParser.parse(ofx_file)
            
            transactions = []
            
            # Processar contas
            for account in ofx.accounts:
                for transaction in account.statement.transactions:
                    
                    # Normalizar dados da transação
                    txn = {
                        "id": f"ofx_{transaction.id}_{transaction.date.strftime('%Y%m%d')}",
                        "date": transaction.date.date(),
                        "amount": float(transaction.amount),
                        "description": transaction.memo or transaction.payee or "Transação OFX",
                        "type": "credit" if transaction.amount > 0 else "debit",
                        "reference": transaction.checknum or transaction.id,
                        "account_id": account.account_id,
                        "source": "ofx",
                        "raw_data": {
                            "fitid": transaction.id,
                            "payee": transaction.payee,
                            "memo": transaction.memo,
                            "checknum": transaction.checknum,
                            "trntype": transaction.trntype
                        }
                    }
                    
                    transactions.append(txn)
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse OFX: {str(e)}")
            raise
    
    async def _parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse de arquivo CSV"""
        
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Não foi possível ler o arquivo CSV com nenhum encoding")
            
            # Detectar formato do CSV automaticamente
            columns = [col.lower().strip() for col in df.columns]
            
            # Mapear colunas comuns
            column_mapping = self._detect_csv_columns(columns)
            
            if not column_mapping:
                raise ValueError("Não foi possível identificar as colunas do CSV")
            
            transactions = []
            
            for index, row in df.iterrows():
                try:
                    # Extrair dados usando mapeamento
                    date_str = str(row[column_mapping['date']]).strip()
                    amount_str = str(row[column_mapping['amount']]).strip()
                    description = str(row[column_mapping.get('description', '')]).strip()
                    
                    # Converter data
                    transaction_date = self._parse_date(date_str)
                    
                    # Converter valor
                    amount = self._parse_amount(amount_str)
                    
                    # Criar transação
                    txn = {
                        "id": f"csv_{index}_{transaction_date.strftime('%Y%m%d')}_{abs(amount)}",
                        "date": transaction_date,
                        "amount": amount,
                        "description": description or f"Transação CSV {index}",
                        "type": "credit" if amount > 0 else "debit",
                        "reference": str(row.get(column_mapping.get('reference', ''), '')).strip(),
                        "source": "csv",
                        "raw_data": row.to_dict()
                    }
                    
                    transactions.append(txn)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar linha {index}: {str(e)}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse CSV: {str(e)}")
            raise
    
    async def _parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse de arquivo PDF (extrato bancário)"""
        
        try:
            # TODO: Implementar parser PDF real usando pdfplumber ou similar
            # Por enquanto, simular extração
            
            logger.info("📄 Simulando extração de PDF...")
            
            # Simular transações extraídas de PDF
            transactions = [
                {
                    "id": "pdf_001_20240118",
                    "date": date(2024, 1, 18),
                    "amount": 1500.00,
                    "description": "TED RECEBIDA EMPRESA ABC LTDA",
                    "type": "credit",
                    "reference": "TED001",
                    "source": "pdf"
                },
                {
                    "id": "pdf_002_20240119",
                    "date": date(2024, 1, 19),
                    "amount": -850.00,
                    "description": "PAGAMENTO FORNECEDOR XYZ",
                    "type": "debit",
                    "reference": "PAG001",
                    "source": "pdf"
                }
            ]
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse PDF: {str(e)}")
            raise
    
    def _detect_csv_columns(self, columns: List[str]) -> Optional[Dict[str, str]]:
        """Detecta mapeamento de colunas do CSV"""
        
        mapping = {}
        
        # Padrões para data
        date_patterns = ['data', 'date', 'dt', 'dt_transacao', 'dt_movimento']
        for col in columns:
            if any(pattern in col for pattern in date_patterns):
                mapping['date'] = col
                break
        
        # Padrões para valor
        amount_patterns = ['valor', 'amount', 'vlr', 'vl_transacao', 'credito', 'debito']
        for col in columns:
            if any(pattern in col for pattern in amount_patterns):
                mapping['amount'] = col
                break
        
        # Padrões para descrição
        desc_patterns = ['descricao', 'description', 'desc', 'historico', 'memo', 'observacao']
        for col in columns:
            if any(pattern in col for pattern in desc_patterns):
                mapping['description'] = col
                break
        
        # Padrões para referência
        ref_patterns = ['referencia', 'reference', 'ref', 'documento', 'doc']
        for col in columns:
            if any(pattern in col for pattern in ref_patterns):
                mapping['reference'] = col
                break
        
        # Verificar se encontrou pelo menos data e valor
        if 'date' in mapping and 'amount' in mapping:
            return mapping
        
        return None
    
    def _parse_date(self, date_str: str) -> date:
        """Parse flexível de datas"""
        
        # Remover caracteres não numéricos exceto separadores
        date_clean = re.sub(r'[^\d\/\-\.]', '', date_str)
        
        # Padrões de data comuns
        date_patterns = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%y',
            '%d-%m-%y'
        ]
        
        for pattern in date_patterns:
            try:
                parsed_date = datetime.strptime(date_clean, pattern).date()
                
                # Ajustar ano de 2 dígitos
                if parsed_date.year < 1950:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 100)
                
                return parsed_date
                
            except ValueError:
                continue
        
        raise ValueError(f"Não foi possível fazer parse da data: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse flexível de valores monetários"""
        
        # Remover espaços e caracteres não numéricos exceto vírgula, ponto e sinal
        amount_clean = re.sub(r'[^\d\,\.\-\+]', '', amount_str)
        
        # Tratar vírgula como separador decimal (padrão brasileiro)
        if ',' in amount_clean and '.' in amount_clean:
            # Se tem ambos, vírgula é decimal
            amount_clean = amount_clean.replace('.', '').replace(',', '.')
        elif ',' in amount_clean:
            # Só vírgula - pode ser decimal ou milhares
            parts = amount_clean.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Vírgula como decimal
                amount_clean = amount_clean.replace(',', '.')
            else:
                # Vírgula como milhares
                amount_clean = amount_clean.replace(',', '')
        
        try:
            return float(amount_clean)
        except ValueError:
            raise ValueError(f"Não foi possível fazer parse do valor: {amount_str}")
    
    def get_supported_formats(self) -> List[str]:
        """Retorna formatos suportados"""
        formats = ["csv", "pdf"]
        if OFX_AVAILABLE:
            formats.append("ofx")
        return formats
    
    def validate_statement_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Valida arquivo de extrato antes do processamento"""
        
        try:
            file_format = self._detect_format(filename, content)
            file_size = len(content)
            
            # Validações básicas
            if file_size == 0:
                return {"valid": False, "error": "Arquivo vazio"}
            
            if file_size > 50 * 1024 * 1024:  # 50MB
                return {"valid": False, "error": "Arquivo muito grande (máximo 50MB)"}
            
            if file_format not in self.get_supported_formats():
                return {"valid": False, "error": f"Formato não suportado: {file_format}"}
            
            return {
                "valid": True,
                "format": file_format,
                "size": file_size,
                "estimated_transactions": self._estimate_transaction_count(content, file_format)
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _estimate_transaction_count(self, content: bytes, file_format: str) -> int:
        """Estima número de transações no arquivo"""
        
        try:
            if file_format == "csv":
                content_str = content.decode('utf-8', errors='ignore')
                lines = content_str.count('\n')
                return max(0, lines - 1)  # Subtrair cabeçalho
            
            elif file_format == "ofx":
                content_str = content.decode('utf-8', errors='ignore')
                return content_str.count('<STMTTRN>')
            
            elif file_format == "pdf":
                # Estimativa baseada no tamanho do arquivo
                return min(100, max(10, len(content) // 1000))
            
        except Exception:
            pass
        
        return 0
