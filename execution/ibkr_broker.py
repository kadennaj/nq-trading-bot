"""
Interactive Brokers (IBKR) Broker Integration
Works with Canadian accounts - supports NQ futures
"""

import logging
from datetime import datetime
from typing import Optional

from ib_insync import IB, Fut, MarketOrder, StopOrder, LimitOrder


class IBKRBroker:
    """Interactive Brokers broker for live futures trading."""
    
    def __init__(self, paper: bool = True):
        """
        Initialize IBKR broker.
        
        Args:
            paper: Use paper trading (TWS Paper Money) if True
        """
        self.logger = logging.getLogger(__name__)
        self.paper = paper
        self.ib = None
        self.contract = None
        self.connected = False
        
    def connect(self, host: str = '127.0.0.1', port: int = 7497):
        """Connect to IBKR TWS or IB Gateway."""
        self.ib = IB()
        
        # Paper trading port is 7497, live is 7496
        port = 7497 if self.paper else 7496
        
        try:
            self.ib.connect(host, port, clientId=1)
            self.connected = True
            self.logger.info(f"Connected to IBKR (paper={self.paper})")
            
            # Set up NQ futures contract
            self.contract =Fut('NQ', 'GLOBEX', 'USD')
            self.ib.qualifyContracts(self.contract)
            self.logger.info(f"Contract qualified: {self.contract}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            raise
    
    def disconnect(self):
        """Disconnect from IBKR."""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from IBKR")
    
    def get_position(self) -> dict:
        """Get current position."""
        if not self.connected:
            return {'size': 0, 'entry_price': 0}
            
        try:
            pos = self.ib.positions()
            for p in pos:
                if p.contract.symbol == 'NQ' and p.contract.exchange == 'GLOBEX':
                    return {
                        'size': p.position,
                        'entry_price': p.avgCost
                    }
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            
        return {'size': 0, 'entry_price': 0}
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price of NQ."""
        if not self.connected or not self.contract:
            return None
            
        try:
            ticker = self.ib.reqMktData(self.contract)
            self.ib.sleep(0.5)  # Wait for data
            return ticker.marketPrice() if ticker.marketPrice() > 0 else None
        except Exception as e:
            self.logger.error(f"Error getting price: {e}")
            return None
    
    def place_order(self, action: str, quantity: int = 1, 
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[int]:
        """
        Place a futures order with optional stop loss and take profit.
        
        Args:
            action: 'BUY' or 'SELL'
            quantity: Number of contracts
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Order ID if successful, None otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return None
            
        try:
            # Create market order
            order = MarketOrder(action, quantity)
            
            # Submit the order
            trade = self.ib.placeOrder(self.contract, order)
            self.ib.sleep(1)  # Wait for execution
            
            order_id = trade.order.orderId
            
            # Attach stop loss if provided
            if stop_loss:
                stop_order = StopOrder(
                    'SELL' if action == 'BUY' else 'BUY',
                    quantity,
                    stop_loss,
                    parentId=order_id
                )
                self.ib.placeOrder(self.contract, stop_order)
                self.logger.info(f"Attached stop loss: {stop_loss}")
            
            # Attach take profit if provided
            if take_profit:
                # Use profit target order (LIT)
                limit_order = LimitOrder(
                    'SELL' if action == 'BUY' else 'BUY',
                    quantity,
                    take_profit,
                    parentId=order_id
                )
                self.ib.placeOrder(self.contract, limit_order)
                self.logger.info(f"Attached take profit: {take_profit}")
            
            self.logger.info(f"Order placed: {action} {quantity} NQ")
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
    
    def close_position(self, reason: str = "signal") -> Optional[float]:
        """Close current position."""
        if not self.connected:
            return None
            
        position = self.get_position()
        if position['size'] == 0:
            return None
            
        try:
            action = 'SELL' if position['size'] > 0 else 'BUY'
            quantity = abs(position['size'])
            
            order = MarketOrder(action, quantity)
            trade = self.ib.placeOrder(self.contract, order)
            self.ib.sleep(1)
            
            self.logger.info(f"Closed position: {action} {quantity} ({reason})")
            return position['entry_price']
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None


def get_broker(paper: bool = True) -> IBKRBroker:
    """Factory function to create IBKR broker."""
    return IBKRBroker(paper=paper)
