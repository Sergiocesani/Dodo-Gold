# Ubicación: trading-system/executions/executor.py

class ExecutionAgent:
    def __init__(self):
        self.trade_history = []

    def execute_trade(self, ticket):
        """
        Simula la ejecución de una orden en el exchange.
        """
        if ticket.risk_status == "APPROVED":
            # Simulamos el éxito de la operación
            ticket.status = "EXECUTED"
            ticket.executed_price = ticket.price_at_signal
            
            print(f"⚡ [EXECUTION] Orden disparada para {ticket.symbol} a ${ticket.executed_price}")
            
            # Guardamos en la memoria del agente
            self.trade_history.append(ticket)
            return True
        
        print(f"🚫 [EXECUTION] Orden rechazada por el Risk Manager. No se ejecuta.")
        return False