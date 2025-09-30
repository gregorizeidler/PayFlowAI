"""
Extrator de dados de extratos bancários
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BankStatementExtractor:
    """Extrator especializado em extratos bancários"""
    
    def __init__(self):
        # Padrões de bancos brasileiros
        self.bank_patterns = {
            "001": "Banco do Brasil",
            "033": "Santander",
            "104": "Caixa Econômica",
            "237": "Bradesco",
            "341": "Itaú",
            "356": "Banco Real",
            "399": "HSBC",
            "422": "Banco Safra"
        }
    
    async def extract(self, text: str, file_path: str = None) -> Dict[str, Any]:
        """
        Extrai dados estruturados de extrato bancário
        """
        try:
            logger.info("🏦 Iniciando extração de dados do extrato bancário")
            
            # Limpar texto
            cleaned_text = self._clean_text(text)
            
            statement_data = {
                "type": "bank_statement",
                "confidence": 0.0,
                "extracted_fields": {}
            }
            
            # 1. Identificar banco
            bank_info = self._extract_bank_info(cleaned_text)
            if bank_info:
                statement_data["extracted_fields"]["bank"] = bank_info
                statement_data["confidence"] += 15
            
            # 2. Número da conta
            account_number = self._extract_account_number(cleaned_text)
            if account_number:
                statement_data["extracted_fields"]["account_number"] = account_number
                statement_data["confidence"] += 10
            
            # 3. Período do extrato
            period = self._extract_period(cleaned_text)
            if period:
                statement_data["extracted_fields"]["period"] = period
                statement_data["confidence"] += 10
            
            # 4. Saldo inicial
            initial_balance = self._extract_balance(cleaned_text, "inicial|anterior")
            if initial_balance is not None:
                statement_data["extracted_fields"]["initial_balance"] = initial_balance
                statement_data["confidence"] += 10
            
            # 5. Saldo final
            final_balance = self._extract_balance(cleaned_text, "final|atual")
            if final_balance is not None:
                statement_data["extracted_fields"]["final_balance"] = final_balance
                statement_data["confidence"] += 10
            
            # 6. Transações
            transactions = self._extract_transactions(cleaned_text)
            if transactions:
                statement_data["extracted_fields"]["transactions"] = transactions
                statement_data["confidence"] += 30
            
            # 7. Resumo financeiro
            summary = self._extract_summary(transactions) if transactions else {}
            if summary:
                statement_data["extracted_fields"]["summary"] = summary
                statement_data["confidence"] += 15
            
            logger.info(f"✅ Extração de extrato concluída. Confiança: {statement_data['confidence']}%")
            return statement_data
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de extrato: {str(e)}")
            return {
                "type": "bank_statement",
                "confidence": 0.0,
                "error": str(e),
                "extracted_fields": {}
            }
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto"""
        # Remover caracteres especiais mas manter formatação de valores
        text = re.sub(r'[^\w\s\.,\-\/\(\):\+]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_bank_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extrai informações do banco"""
        # Procurar por códigos de banco
        for code, name in self.bank_patterns.items():
            if code in text or name.lower() in text.lower():
                return {
                    "code": code,
                    "name": name
                }
        
        # Procurar por padrões genéricos
        bank_pattern = r'banco\s+([a-zA-Z\s]+)'
        match = re.search(bank_pattern, text, re.IGNORECASE)
        if match:
            return {
                "name": match.group(1).strip()
            }
        
        return None
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """Extrai número da conta"""
        patterns = [
            r'conta\s*:?\s*(\d+\-?\d*)',
            r'ag[êe]ncia\s*:?\s*(\d+)\s*conta\s*:?\s*(\d+\-?\d*)',
            r'(\d{4,8}\-?\d{1})'  # Padrão conta corrente
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    return f"{match.group(1)}-{match.group(2)}"
                return match.group(1)
        
        return None
    
    def _extract_period(self, text: str) -> Optional[Dict[str, str]]:
        """Extrai período do extrato"""
        # Procurar por datas de início e fim
        date_pattern = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 2:
            try:
                start_date = self._parse_date(dates[0])
                end_date = self._parse_date(dates[-1])
                
                if start_date and end_date:
                    return {
                        "start_date": start_date,
                        "end_date": end_date
                    }
            except:
                pass
        
        return None
    
    def _extract_balance(self, text: str, balance_type: str) -> Optional[float]:
        """Extrai saldo (inicial ou final)"""
        pattern = f"saldo\\s+{balance_type}\\s*:?\\s*(\\d{{1,3}}(?:\\.\\d{{3}})*,\\d{{2}})"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                balance_str = match.group(1).replace('.', '').replace(',', '.')
                return float(balance_str)
            except ValueError:
                pass
        
        return None
    
    def _extract_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Extrai transações do extrato"""
        transactions = []
        
        # Padrões comuns de transação
        # Data + Descrição + Valor
        transaction_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2})\s+([A-Za-z\s\-]+?)\s+(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+([A-Za-z\s\-]+?)\s+(\d{1,3}(?:\.\d{3})*,\d{2})'
        ]
        
        for pattern in transaction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    date_str = match[0]
                    description = match[1].strip()
                    amount_str = match[2]
                    
                    # Parse da data
                    parsed_date = self._parse_date(date_str)
                    if not parsed_date:
                        continue
                    
                    # Parse do valor
                    amount = float(amount_str.replace('.', '').replace(',', '.'))
                    
                    # Determinar tipo (débito/crédito)
                    transaction_type = self._determine_transaction_type(description, text, amount_str)
                    
                    transaction = {
                        "date": parsed_date,
                        "description": description[:100],  # Limitar descrição
                        "amount": amount,
                        "type": transaction_type
                    }
                    
                    transactions.append(transaction)
                    
                except (ValueError, IndexError):
                    continue
        
        # Remover duplicatas e ordenar por data
        unique_transactions = []
        seen = set()
        
        for trans in transactions:
            key = (trans["date"], trans["amount"], trans["description"][:20])
            if key not in seen:
                seen.add(key)
                unique_transactions.append(trans)
        
        # Ordenar por data
        unique_transactions.sort(key=lambda x: x["date"])
        
        return unique_transactions[:50]  # Limitar a 50 transações
    
    def _determine_transaction_type(self, description: str, full_text: str, amount_str: str) -> str:
        """Determina se é débito ou crédito"""
        description_lower = description.lower()
        
        # Palavras-chave para crédito
        credit_keywords = ['deposito', 'credito', 'recebimento', 'transferencia recebida', 'pix recebido']
        
        # Palavras-chave para débito
        debit_keywords = ['saque', 'debito', 'pagamento', 'transferencia enviada', 'pix enviado', 'tarifa']
        
        if any(keyword in description_lower for keyword in credit_keywords):
            return "credit"
        elif any(keyword in description_lower for keyword in debit_keywords):
            return "debit"
        
        # Se não conseguir determinar pelo contexto, assumir débito para valores pequenos
        try:
            amount = float(amount_str.replace('.', '').replace(',', '.'))
            return "debit" if amount < 1000 else "credit"
        except:
            return "debit"
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse de data em diferentes formatos"""
        try:
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%d/%m']:
                try:
                    if fmt == '%d/%m':
                        # Assumir ano atual
                        date_str_full = f"{date_str}/{datetime.now().year}"
                        parsed_date = datetime.strptime(date_str_full, '%d/%m/%Y')
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                    
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except:
            pass
        
        return None
    
    def _extract_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera resumo das transações"""
        if not transactions:
            return {}
        
        total_credits = sum(t["amount"] for t in transactions if t["type"] == "credit")
        total_debits = sum(t["amount"] for t in transactions if t["type"] == "debit")
        
        return {
            "total_transactions": len(transactions),
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "net_flow": round(total_credits - total_debits, 2),
            "credit_count": len([t for t in transactions if t["type"] == "credit"]),
            "debit_count": len([t for t in transactions if t["type"] == "debit"])
        }
