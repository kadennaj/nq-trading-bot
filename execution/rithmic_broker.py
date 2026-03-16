"""
Rithmic/Quantower Broker Integration
For Lucid Trading funded accounts
Uses Rithmic API via Quantower
"""

import logging
import time
import json
from typing import Optional
from datetime import datetime


class RithmicBroker:
    """
    Rithmic broker for Lucid Trading / Quantower
    Connects via Rithmic DLL or local Rithmic bridge
    """
    
    def __init__(self, paper: bool = True, symbol: str = 'NQ'):
        self.logger = logging.getLogger(__name__)
        self.paper = paper
        self.symbol = symbol
        
        # Rithmic connection settings
        # For Lucid Trading: use their Rithmic credentials
        self.host = "localhost"  # Quantower runs Rithmic locally
        self.port = 8899 if paper else 8898
        
        # State
        self.connected = False
        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
        # Paper trading mode (simulated)
        self.paper_balance = 25000
        
        self.logger.info(f"Initialized Rithmic broker: {self.symbol} | Paper: {paper}")
    
    def connect(self) -> bool:
        """Connect to Rithmic/Quantower."""
        try:
            # In production, this would connect to Rithmic
            # For now, we simulate connection for paper trading
            self.connected = True
            self.logger.info("Connected to Rithmic (paper mode)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
    
    def get_market_data(self) -> Optional[dict]:
        """Get current market price."""
        # In production, fetch real-time data from Rithmic
        # For paper, return simulated price
        return {
            'bid': 21000,
            'ask': 21000.5,
            'last': 21000.25,
            'timestamp': datetime.now()
        }
    
    def place_order(self, action: str, quantity: int = 1, 
                   order_type: str = 'market',
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[dict]:
        """
        Place an order with bracket (stop loss / take profit)
        """
        if not self.connected:
            self.logger.warning("Not connected, cannot place order")
            return None
        
        try:
            # For paper trading, simulate order execution
            market_data = self.get_market_data()
            fill_price = market_data['last']
            
            order = {
                'order_id': f"sim_{int(time.time())}",
                'action': action,
                'quantity': quantity,
                'fill_price': fill_price,
                'timestamp': datetime.now(),
                'status': 'filled'
            }
            
            # Update position
            if action == 'buy':
                self.position = quantity
            elif action == 'sell':
                self.position = -quantity
            
            self.entry_price = fill_price
            self.stop_loss = stop_loss
            self.take_profit = take_profit
            
            self.logger.info(f"ORDER FILLED: {action.upper()} {quantity} @ {fill_price}")
            self.logger.info(f"  SL: {stop_loss} | TP: {take_profit}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Order failed: {e}")
            return None
    
    def close_position(self, exit_price: float = None) -> Optional[dict]:
        """Close current position."""
        if self.position == 0:
            return None
        
        if exit_price is None:
            market_data = self.get_market_data()
            exit_price = market_data['last']
        
        action = 'sell' if self.position > 0 else 'buy'
        pnl = (exit_price - self.entry_price) * abs(self.position)
        
        self.logger.info(f"CLOSED: {action.upper()} {abs(self.position)} @ {exit_price} | PnL: {pnl:.2f}")
        
        closed_order = {
            'action': action,
            'quantity': abs(self.position),
            'fill_price': exit_price,
            'pnl': pnl,
            'timestamp': datetime.now()
        }
        
        self.position = 0
        self.entry_price = 0
        
        return closed_order
    
    def get_position(self) -> dict:
        """Get current position."""
        return {
            'size': self.position,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }
    
    def get_account(self) -> dict:
        """Get account info."""
        return {
            'balance': self.paper_balance,
            'position_value': self.position * self.entry_price if self.position != 0 else 0,
            'equity': self.paper_balance
        }
    
    def check_exits(self, current_price: float) -> Optional[dict]:
        """Check if stop loss or take profit is hit."""
        if self.position == 0:
            return None
        
        exit_reason = None
        exit_price = None
        
        if self.position > 0:  # Long
            if self.stop_loss and current_price <= self.stop_loss:
                exit_reason = 'stop_loss'
                exit_price = self.stop_loss
            elif self.take_profit and current_price >= self.take_profit:
                exit_reason = 'take_profit'
                exit_price = self.take_profit
        else:  # Short
            if self.stop_loss and current_price >= self.stop_loss:
                exit_reason = 'stop_loss'
                exit_price = self.stop_loss
            elif self.take_profit and current_price <= self.take_profit:
                exit_reason = 'take_profit'
                exit_price = self.take_profit
        
        if exit_reason:
            return self.close_position(exit_price)
        
        return None
    
    def disconnect(self):
        """Disconnect from Rithmic."""
        self.connected = False
        self.logger.info("Disconnected from Rithmic")


def create_rithmic_broker(paper: bool = True, symbol: str = 'NQ'):
    """Factory function to create Rithmic broker."""
    return RithmicBroker(paper=paper, symbol=symbol)
