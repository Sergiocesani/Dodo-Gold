# Ubicación: trading-system/risk/risk_manager.py

from core.schemas import TradeTicket

class RiskManager:
    def __init__(self, max_exposure_pct=0.10, daily_stop_loss_pct=0.02):
        self.max_exposure_pct = max_exposure_pct  # No más del 10% por trade
        self.daily_stop_loss_pct = daily_stop_loss_pct # No perder más del 2% diario
        self.current_daily_pnl = 0.0 # Esto se conectará con Analytics después

    def validate_trade(self, ticket: TradeTicket, account_balance: float) -> TradeTicket:
        """
        El 'Filtro de Seguridad'. Revisa el ticket antes de la ejecución.
        """
        
        # 🛡️ REGLA 1: Exposición Máxima
        # No queremos que un solo trade arriesgue demasiado capital
        max_allowed_amount = account_balance * self.max_exposure_pct
        
        if ticket.amount > max_allowed_amount:
            ticket.risk_status = "REJECTED"
            ticket.risk_notes = f"Exceso de exposición: {ticket.amount} > {max_allowed_amount}"
            return ticket

        # 📉 REGLA 2: Daily Stop-Out
        # Si ya perdimos mucho hoy, no se opera más
        if self.current_daily_pnl <= -(account_balance * self.daily_stop_loss_pct):
            ticket.risk_status = "REJECTED"
            ticket.risk_notes = "Daily Stop-Loss alcanzado. Sistema bloqueado por hoy."
            return ticket

        # ✅ SI PASA TODO:
        ticket.risk_status = "APPROVED"
        ticket.risk_notes = "Validación de riesgo exitosa."
        return ticket