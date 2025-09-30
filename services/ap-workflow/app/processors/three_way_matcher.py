"""
Processador de 3-Way Matching
Compara Purchase Order + Goods Receipt + Invoice
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, date
import httpx

from app.models.workflow_models import MatchingResult, MatchingException
from app.config import settings

logger = logging.getLogger(__name__)

class ThreeWayMatcher:
    """Processador de 3-Way Matching"""
    
    def __init__(self):
        self.price_tolerance = settings.price_tolerance_percent / 100
        self.quantity_tolerance = settings.quantity_tolerance_percent / 100
        self.date_tolerance_days = settings.date_tolerance_days
    
    async def perform_matching(self, invoice_data: Dict[str, Any]) -> MatchingResult:
        """
        Executa o 3-Way Matching completo:
        1. Busca Purchase Order (PO)
        2. Busca Goods Receipt (GR)
        3. Compara Invoice vs PO vs GR
        4. Identifica exceções
        """
        try:
            invoice_id = invoice_data.get("id")
            supplier_id = invoice_data.get("supplier_id")
            
            logger.info(f"⚖️ Iniciando 3-Way Matching para fatura {invoice_id}")
            
            # 1. Buscar Purchase Order
            purchase_order = await self._find_purchase_order(invoice_data)
            if not purchase_order:
                return MatchingResult(
                    invoice_id=invoice_id,
                    matched=False,
                    has_exceptions=True,
                    exceptions=[MatchingException(
                        type="no_purchase_order",
                        description="Nenhuma Purchase Order encontrada para esta fatura",
                        severity="high"
                    )]
                )
            
            # 2. Buscar Goods Receipt
            goods_receipt = await self._find_goods_receipt(purchase_order)
            if not goods_receipt:
                return MatchingResult(
                    invoice_id=invoice_id,
                    matched=False,
                    has_exceptions=True,
                    exceptions=[MatchingException(
                        type="no_goods_receipt",
                        description="Nenhum recebimento encontrado para a Purchase Order",
                        severity="high"
                    )]
                )
            
            # 3. Executar comparações
            exceptions = []
            
            # Comparar preços
            price_exceptions = await self._compare_prices(invoice_data, purchase_order)
            exceptions.extend(price_exceptions)
            
            # Comparar quantidades
            quantity_exceptions = await self._compare_quantities(invoice_data, purchase_order, goods_receipt)
            exceptions.extend(quantity_exceptions)
            
            # Comparar datas
            date_exceptions = await self._compare_dates(invoice_data, purchase_order, goods_receipt)
            exceptions.extend(date_exceptions)
            
            # Comparar fornecedores
            supplier_exceptions = await self._compare_suppliers(invoice_data, purchase_order)
            exceptions.extend(supplier_exceptions)
            
            # Determinar resultado
            has_exceptions = len(exceptions) > 0
            matched = not has_exceptions
            
            result = MatchingResult(
                invoice_id=invoice_id,
                matched=matched,
                has_exceptions=has_exceptions,
                exceptions=exceptions,
                purchase_order_id=purchase_order.get("id"),
                goods_receipt_id=goods_receipt.get("id"),
                matching_score=self._calculate_matching_score(exceptions),
                processed_at=datetime.utcnow()
            )
            
            logger.info(f"✅ 3-Way Matching concluído para fatura {invoice_id}: "
                       f"{'✓ Matched' if matched else '⚠ Exceptions'}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no 3-Way Matching: {str(e)}")
            return MatchingResult(
                invoice_id=invoice_id,
                matched=False,
                has_exceptions=True,
                exceptions=[MatchingException(
                    type="processing_error",
                    description=f"Erro no processamento: {str(e)}",
                    severity="high"
                )],
                error=str(e)
            )
    
    async def _find_purchase_order(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca Purchase Order relacionada à fatura"""
        try:
            # Estratégias de busca:
            # 1. Por número da PO na fatura
            # 2. Por fornecedor + valor + período
            # 3. Por itens similares
            
            supplier_id = invoice_data.get("supplier_id")
            total_amount = Decimal(str(invoice_data.get("total_amount", 0)))
            invoice_date = datetime.fromisoformat(invoice_data.get("invoice_date"))
            
            # Simular busca no Core API
            async with httpx.AsyncClient() as client:
                # Buscar POs do fornecedor no período
                response = await client.get(
                    f"{settings.core_api_url}/api/v1/purchase-orders",
                    params={
                        "supplier_id": supplier_id,
                        "status": "approved",
                        "date_from": (invoice_date.date() - date.timedelta(days=90)).isoformat(),
                        "date_to": invoice_date.date().isoformat()
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    purchase_orders = response.json()
                    
                    # Encontrar PO com valor mais próximo
                    best_match = None
                    best_score = 0
                    
                    for po in purchase_orders:
                        po_amount = Decimal(str(po.get("total_amount", 0)))
                        amount_diff = abs(total_amount - po_amount) / total_amount
                        
                        if amount_diff <= self.price_tolerance:
                            score = 1 - amount_diff
                            if score > best_score:
                                best_score = score
                                best_match = po
                    
                    return best_match
            
            # Se não encontrou via API, simular PO para demonstração
            return {
                "id": f"po-{supplier_id}-001",
                "supplier_id": supplier_id,
                "total_amount": float(total_amount),
                "status": "approved",
                "items": [
                    {
                        "description": "Item simulado",
                        "quantity": 10,
                        "unit_price": float(total_amount) / 10,
                        "total_price": float(total_amount)
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar Purchase Order: {str(e)}")
            return None
    
    async def _find_goods_receipt(self, purchase_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca Goods Receipt relacionado à Purchase Order"""
        try:
            po_id = purchase_order.get("id")
            
            # Simular busca no Core API
            # Em um sistema real, buscaria no banco de dados
            
            # Simular GR para demonstração
            return {
                "id": f"gr-{po_id}-001",
                "po_id": po_id,
                "received_date": datetime.now().date().isoformat(),
                "status": "completed",
                "items": purchase_order.get("items", [])  # Simular recebimento completo
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar Goods Receipt: {str(e)}")
            return None
    
    async def _compare_prices(self, invoice: Dict[str, Any], purchase_order: Dict[str, Any]) -> List[MatchingException]:
        """Compara preços entre fatura e PO"""
        exceptions = []
        
        try:
            invoice_amount = Decimal(str(invoice.get("total_amount", 0)))
            po_amount = Decimal(str(purchase_order.get("total_amount", 0)))
            
            if po_amount > 0:
                variance_percent = abs(invoice_amount - po_amount) / po_amount
                
                if variance_percent > self.price_tolerance:
                    exceptions.append(MatchingException(
                        type="price_mismatch",
                        description=f"Diferença de preço: Fatura R$ {invoice_amount:.2f} vs PO R$ {po_amount:.2f}",
                        severity="medium" if variance_percent < 0.1 else "high",
                        variance_amount=float(abs(invoice_amount - po_amount)),
                        variance_percent=float(variance_percent * 100)
                    ))
            
        except Exception as e:
            logger.error(f"❌ Erro ao comparar preços: {str(e)}")
        
        return exceptions
    
    async def _compare_quantities(self, invoice: Dict[str, Any], purchase_order: Dict[str, Any], goods_receipt: Dict[str, Any]) -> List[MatchingException]:
        """Compara quantidades entre fatura, PO e GR"""
        exceptions = []
        
        try:
            # Comparar itens (simplificado para demonstração)
            invoice_items = invoice.get("items", [])
            po_items = purchase_order.get("items", [])
            gr_items = goods_receipt.get("items", [])
            
            for i, invoice_item in enumerate(invoice_items):
                if i < len(po_items) and i < len(gr_items):
                    invoice_qty = Decimal(str(invoice_item.get("quantity", 0)))
                    po_qty = Decimal(str(po_items[i].get("quantity", 0)))
                    gr_qty = Decimal(str(gr_items[i].get("quantity_received", po_items[i].get("quantity", 0))))
                    
                    # Verificar se quantidade faturada > quantidade recebida
                    if invoice_qty > gr_qty:
                        exceptions.append(MatchingException(
                            type="quantity_over_receipt",
                            description=f"Quantidade faturada ({invoice_qty}) maior que recebida ({gr_qty})",
                            severity="high",
                            variance_amount=float(invoice_qty - gr_qty)
                        ))
                    
                    # Verificar tolerância com PO
                    if po_qty > 0:
                        variance_percent = abs(invoice_qty - po_qty) / po_qty
                        if variance_percent > self.quantity_tolerance:
                            exceptions.append(MatchingException(
                                type="quantity_mismatch",
                                description=f"Diferença de quantidade: Fatura {invoice_qty} vs PO {po_qty}",
                                severity="medium",
                                variance_amount=float(abs(invoice_qty - po_qty)),
                                variance_percent=float(variance_percent * 100)
                            ))
            
        except Exception as e:
            logger.error(f"❌ Erro ao comparar quantidades: {str(e)}")
        
        return exceptions
    
    async def _compare_dates(self, invoice: Dict[str, Any], purchase_order: Dict[str, Any], goods_receipt: Dict[str, Any]) -> List[MatchingException]:
        """Compara datas entre documentos"""
        exceptions = []
        
        try:
            invoice_date = datetime.fromisoformat(invoice.get("invoice_date")).date()
            gr_date = datetime.fromisoformat(goods_receipt.get("received_date")).date()
            
            # Verificar se fatura é anterior ao recebimento
            if invoice_date < gr_date:
                days_diff = (gr_date - invoice_date).days
                if days_diff > self.date_tolerance_days:
                    exceptions.append(MatchingException(
                        type="date_sequence_error",
                        description=f"Fatura datada {days_diff} dias antes do recebimento",
                        severity="medium",
                        variance_amount=days_diff
                    ))
            
        except Exception as e:
            logger.error(f"❌ Erro ao comparar datas: {str(e)}")
        
        return exceptions
    
    async def _compare_suppliers(self, invoice: Dict[str, Any], purchase_order: Dict[str, Any]) -> List[MatchingException]:
        """Compara fornecedores entre fatura e PO"""
        exceptions = []
        
        try:
            invoice_supplier = invoice.get("supplier_id")
            po_supplier = purchase_order.get("supplier_id")
            
            if invoice_supplier != po_supplier:
                exceptions.append(MatchingException(
                    type="supplier_mismatch",
                    description=f"Fornecedor da fatura ({invoice_supplier}) difere da PO ({po_supplier})",
                    severity="high"
                ))
            
        except Exception as e:
            logger.error(f"❌ Erro ao comparar fornecedores: {str(e)}")
        
        return exceptions
    
    def _calculate_matching_score(self, exceptions: List[MatchingException]) -> float:
        """Calcula score de matching baseado nas exceções"""
        if not exceptions:
            return 100.0
        
        # Penalizar baseado na severidade
        penalty = 0
        for exception in exceptions:
            if exception.severity == "high":
                penalty += 30
            elif exception.severity == "medium":
                penalty += 15
            else:
                penalty += 5
        
        return max(0.0, 100.0 - penalty)
