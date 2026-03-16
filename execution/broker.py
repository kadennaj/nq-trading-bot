"""
Broker Integration
Handles trade execution and position management
"""

import logging
from datetime import datetime
from typing import Optional


class Broker:
    """
    Broker interface for trade execution.
    Supports paper trading and live execution.
    """
    
    def __init__(self, mode: str = 'paper', symbol: str = 'NQ'):
        self.logger = logging.getLogger(__name__)
        self.mode = mode
        self.symbol = symbol
        
        # Paper trading state
        self.paper_position = 0
        self.paper_entry_price = 0
        self.paper_stop_loss = 0
        self.paper_take_profit = 0
        
        # Simulated account
        self.paper_balance = 100000  # $100k simulated
        
    def execute(
        self,
        action: str,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> dict:
        """
        Execute a live trade (requires broker integration).
        
        Args:
            action: 'buy' or 'sell'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Execution result
        """
        if self.mode == 'live':
            self.logger.warning("Live trading not yet implemented")
            # Would integrate with broker API here
            # (Interactive Brokers, Alpaca, TrendFutures, etc.)
            return None
            
        return self.paper_trade(action, entry_price, stop_loss, take_profit)
    
    def paper_trade(
        self,
        action: str,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> dict:
        """
        Execute a paper trade.
        
        Args:
            action: 'buy' or 'sell'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Paper trade result
        """
        if action == 'buy':
            self.paper_position = 1
        elif action == 'sell':
            self.paper_position = -1
        else:
            return None
            
        self.paper_entry_price = entry_price
        self.paper_stop_loss = stop_loss or 0
        self.paper_take_profit = take_profit or 0
        
        self.logger.info(
            f"PAPER TRADE: {action.upper()} {self.symbol} @ {entry_price} | "
            f"SL: {stop_loss} | TP: {take_profit}"
        )
        
        return {
            'timestamp': datetime.now(),
            'action': action,
            'entry': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'mode': 'paper'
        }
    
    def get_position(self) -> dict:
        """Get current position."""
        return {
            'size': self.paper_position,
            'entry_price': self.paper_entry_price,
            'stop_loss': self.paper_stop_loss,
            'take_profit': self.paper_take_profit,
            'mode': self.mode
        }
    
    def close_position(self, exit_price: float) -> dict:
        """
        Close current position.
        
        Args:
            exit_price: Exit price
            
        Returns:
            Trade result with P&L
        """
        if self.paper_position == 0:
            return None
            
        if self.paper_position == 1:
            pnl = exit_price - self.paper_entry_price
        else:
            pnl = self.paper_entry_price - exit_price
            
        # NQ: 1 point = $20
        pnl_dollars = pnl * 20
        
        self.logger.info(
            f"CLOSED: {self.symbol} @ {exit_price} | "
            f"PnL: {pnl:.2f} points (${pnl_dollars:.2f})"
        )
        
        result = {
            'entry': self.paper_entry_price,
            'exit': exit_price,
            'pnl_points': pnl,
            'pnl_dollars': pnl_dollars,
            'position': self.paper_position
        }
        
        # Reset position
        self.paper_position = 0
        self.paper_entry_price = 0
        self.paper_stop_loss = 0
        self.paper_take_profit = 0
        
        return result
    
    def check_exits(self, current_price: float) -> Optional[dict]:
        """
        Check if stop loss or take profit is hit.
        
        Args:
            current_price: Current market price
            
        Returns:
            Exit result if triggered, None otherwise
        """
        if self.paper_position == 0:
            return None
            
        exit_reason = None
        
        if self.paper_position == 1:
            # Long position
            if self.paper_stop_loss and current_price <= self.paper_stop_loss:
                exit_reason = 'stop_loss'
                exit_price = self.paper_stop_loss
            elif self.paper_take_profit and current_price >= self.paper_take_profit:
                exit_reason = 'take_profit'
                exit_price = self.paper_take_profit
        else:
            # Short position
            if self.paper_stop_loss and current_price >= self.paper_stop_loss:
                exit_reason = 'stop_loss'
                exit_price = self.paper_stop_loss
            elif self.paper_take_profit and current_price <= self.paper_take_profit:
                exit_reason = 'take_profit'
                exit_price = self.paper_take_profit
        
        if exit_reason:
            return self.close_position(exit_price)
            
        return None
    
    def get_account_balance(self) -> float:
        """Get paper trading account balance."""
        return self.paper_balance
