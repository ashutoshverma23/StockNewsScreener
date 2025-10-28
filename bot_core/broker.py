# bot_core/broker.py
from datetime import datetime

class MockBroker:
    def __init__(self):
        self.trades = []
        self.balance = 100000  # Example virtual balance
    
    def stats(self):
        return {
            "balance": self.balance,
            "trades_count": len(self.trades),
            "pnl": sum(t["pnl"] for t in self.trades if "pnl" in t)
        }

    def execute_trade(self, symbol, side, qty, price):
        trade = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry": price,
            "entry_time": datetime.now(),
        }
        self.trades.append(trade)
        return trade

# Global instance
broker = MockBroker()

# Active positions dictionary
active_positions = {}
