# Ubicación: trading-system/core/schemas.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

@dataclass
class TradeTicket:
    # 1. Identificación y Tiempo
    id: str
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = "BTCUSDT"
    
    # 2. Datos del Agente de Análisis
    market_context: Dict = field(default_factory=dict) # RSI, Tendencia, etc.
    
    # 3. Decisión del Agente de Estrategia
    signal: str = "HOLD"  # BUY, SELL, HOLD
    amount: float = 0.0
    price_at_signal: float = 0.0
    
    # 4. Verificación del Agente de Riesgo
    risk_status: str = "PENDING" # APPROVED, REJECTED, PENDING
    risk_notes: Optional[str] = None
    
    # 5. Resultado del Agente de Ejecución
    execution_id: Optional[str] = None
    executed_price: Optional[float] = None
    status: str = "OPEN" # OPEN, CLOSED, CANCELLED