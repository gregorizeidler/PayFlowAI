"""
Manipulador de Exceções do 3-Way Matching
Tenta resolver exceções automaticamente quando possível
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal

from app.models.workflow_models import MatchingException
from app.config import settings

logger = logging.getLogger(__name__)

class ExceptionHandler:
    """Manipulador de exceções do matching"""
    
    def __init__(self):
        self.auto_resolve_threshold = 0.05  # 5% de tolerância para auto-resolução
    
    async def handle_exceptions(self, exceptions: List[MatchingException]) -> Dict[str, Any]:
        """
        Tenta resolver exceções automaticamente:
        1. Diferenças de preço pequenas
        2. Diferenças de quantidade menores
        3. Problemas de data dentro da tolerância
        """
        try:
            logger.info(f"🔧 Processando {len(exceptions)} exceções")
            
            auto_resolved = []
            manual_review = []
            
            for exception in exceptions:
                resolution_result = await self._try_resolve_exception(exception)
                
                if resolution_result["resolved"]:
                    auto_resolved.append({
                        "exception": exception,
                        "resolution": resolution_result["resolution"]
                    })
                else:
                    manual_review.append(exception)
            
            result = {
                "auto_resolved": len(manual_review) == 0,
                "total_exceptions": len(exceptions),
                "auto_resolved_count": len(auto_resolved),
                "manual_review_count": len(manual_review),
                "auto_resolved_exceptions": auto_resolved,
                "manual_review_exceptions": manual_review
            }
            
            logger.info(f"✅ Resolução automática: {len(auto_resolved)}/{len(exceptions)} exceções")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar exceções: {str(e)}")
            return {
                "auto_resolved": False,
                "error": str(e),
                "manual_review_exceptions": exceptions
            }
    
    async def _try_resolve_exception(self, exception: MatchingException) -> Dict[str, Any]:
        """Tenta resolver uma exceção específica"""
        
        try:
            # Resolver diferenças de preço pequenas
            if exception.type == "price_mismatch":
                return await self._resolve_price_mismatch(exception)
            
            # Resolver diferenças de quantidade pequenas
            elif exception.type == "quantity_mismatch":
                return await self._resolve_quantity_mismatch(exception)
            
            # Resolver problemas de data menores
            elif exception.type == "date_sequence_error":
                return await self._resolve_date_issue(exception)
            
            # Exceções críticas não podem ser resolvidas automaticamente
            else:
                return {
                    "resolved": False,
                    "reason": "Exceção crítica requer revisão manual"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao resolver exceção: {str(e)}")
            return {
                "resolved": False,
                "reason": f"Erro no processamento: {str(e)}"
            }
    
    async def _resolve_price_mismatch(self, exception: MatchingException) -> Dict[str, Any]:
        """Tenta resolver diferenças de preço"""
        
        if exception.variance_percent and exception.variance_percent <= (self.auto_resolve_threshold * 100):
            return {
                "resolved": True,
                "resolution": f"Diferença de preço de {exception.variance_percent:.2f}% está dentro da tolerância automática",
                "action": "approved_with_variance",
                "tolerance_used": f"{exception.variance_percent:.2f}%"
            }
        
        # Verificar se é um arredondamento comum
        if exception.variance_amount and exception.variance_amount <= 1.0:
            return {
                "resolved": True,
                "resolution": "Diferença de R$ {:.2f} considerada arredondamento".format(exception.variance_amount),
                "action": "approved_rounding",
                "variance": exception.variance_amount
            }
        
        return {
            "resolved": False,
            "reason": f"Diferença de preço de {exception.variance_percent:.2f}% excede tolerância automática"
        }
    
    async def _resolve_quantity_mismatch(self, exception: MatchingException) -> Dict[str, Any]:
        """Tenta resolver diferenças de quantidade"""
        
        if exception.variance_percent and exception.variance_percent <= (self.auto_resolve_threshold * 100):
            return {
                "resolved": True,
                "resolution": f"Diferença de quantidade de {exception.variance_percent:.2f}% está dentro da tolerância",
                "action": "approved_with_variance",
                "tolerance_used": f"{exception.variance_percent:.2f}%"
            }
        
        # Verificar se é uma unidade de diferença (comum em embalagens)
        if exception.variance_amount and exception.variance_amount == 1:
            return {
                "resolved": True,
                "resolution": "Diferença de 1 unidade considerada variação de embalagem",
                "action": "approved_packaging_variance"
            }
        
        return {
            "resolved": False,
            "reason": f"Diferença de quantidade de {exception.variance_percent:.2f}% excede tolerância"
        }
    
    async def _resolve_date_issue(self, exception: MatchingException) -> Dict[str, Any]:
        """Tenta resolver problemas de data"""
        
        if exception.variance_amount and exception.variance_amount <= settings.date_tolerance_days:
            return {
                "resolved": True,
                "resolution": f"Diferença de {exception.variance_amount} dias está dentro da tolerância",
                "action": "approved_date_variance",
                "days_difference": exception.variance_amount
            }
        
        return {
            "resolved": False,
            "reason": f"Diferença de {exception.variance_amount} dias excede tolerância de {settings.date_tolerance_days} dias"
        }
    
    async def create_manual_review_task(self, exceptions: List[MatchingException], invoice_id: str) -> Dict[str, Any]:
        """Cria tarefa de revisão manual para exceções não resolvidas"""
        
        try:
            # Classificar exceções por prioridade
            high_priority = [exc for exc in exceptions if exc.severity == "high"]
            medium_priority = [exc for exc in exceptions if exc.severity == "medium"]
            low_priority = [exc for exc in exceptions if exc.severity == "low"]
            
            task = {
                "invoice_id": invoice_id,
                "task_type": "exception_review",
                "priority": "high" if high_priority else ("medium" if medium_priority else "low"),
                "total_exceptions": len(exceptions),
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority),
                "low_priority_count": len(low_priority),
                "exceptions": [exc.to_dict() for exc in exceptions],
                "created_at": "now",
                "estimated_review_time": self._estimate_review_time(exceptions)
            }
            
            logger.info(f"📋 Tarefa de revisão manual criada para fatura {invoice_id}")
            
            return task
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar tarefa de revisão: {str(e)}")
            raise
    
    def _estimate_review_time(self, exceptions: List[MatchingException]) -> str:
        """Estima tempo necessário para revisão manual"""
        
        # Tempo base por exceção (em minutos)
        time_per_exception = {
            "high": 15,
            "medium": 8,
            "low": 3
        }
        
        total_minutes = sum(
            time_per_exception.get(exc.severity, 10) for exc in exceptions
        )
        
        if total_minutes < 60:
            return f"{total_minutes} minutos"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}min" if minutes > 0 else f"{hours}h"
    
    def get_exception_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de exceções"""
        # TODO: Implementar busca real no banco
        return {
            "total_exceptions_last_30_days": 145,
            "auto_resolved_percentage": 68.2,
            "most_common_exceptions": [
                {"type": "price_mismatch", "count": 45, "auto_resolve_rate": 78.0},
                {"type": "quantity_mismatch", "count": 32, "auto_resolve_rate": 65.0},
                {"type": "date_sequence_error", "count": 28, "auto_resolve_rate": 85.0}
            ],
            "average_resolution_time": "12.5 minutes",
            "manual_review_backlog": 8
        }
