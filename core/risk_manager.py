"""
Risk Management Module
Handles position sizing, stop losses, and risk controls
"""

import logging
from typing import Optional


class RiskManager:
    """Manages risk parameters for trading."""
    
    def __init__(
        self,
        max_position_pct: float = 2.0,      # Max 2% of account per trade
        max_daily_loss_pct: float = 3.0,    # Max 3% daily loss
        max_drawdown_pct: float = 10.0,      # Max 10% drawdown
        risk_per_trade_pct: float = 0.5,     # Risk 0.5% per trade
        reward_risk_ratio: float = 2.0,     # 2:1 reward:risk
    ):
        self.logger = logging.getLogger(__name__)
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        self.reward_risk_ratio = reward_risk_ratio
        
        # Track daily P&L
        self.daily_pnl = 0
        self.peak_equity = 0
        self.current_equity = 0
        
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        nq_tick_value: float = 20.0  # NQ: $20/tick
    ) -> int:
        """
        Calculate position size based on risk parameters.
        
        Args:
            account_balance: Total account value
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            nq_tick_value: Value per tick for NQ ($20)
            
        Returns:
            Number of contracts to trade
        """
        risk_amount = account_balance * (self.risk_per_trade_pct / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        # Position size = risk amount / (price risk * tick value / point value)
        # NQ: 1 point = 20 ticks = $400
        point_value = nq_tick_value * 20
        contracts = risk_amount / (price_risk * point_value / 100)
        
        return max(1, int(contracts))
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str,
        atr_multiplier: float = 1.5
    ) -> float:
        """
        Calculate stop loss based on ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            direction: 'long' or 'short'
            atr_multiplier: ATR multiplier for stop distance
            
        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier
        
        if direction == 'long':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str
    ) -> float:
        """
        Calculate take profit based on reward:risk ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: 'long' or 'short'
            
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * self.reward_risk_ratio
        
        if direction == 'long':
            return entry_price + reward
        else:
            return entry_price - reward
    
    def check_daily_limits(self, current_pnl: float) -> bool:
        """
        Check if daily loss limit is reached.
        
        Args:
            current_pnl: Current day's P&L
            
        Returns:
            True if trading is allowed, False if limit reached
        """
        if abs(current_pnl) >= self.max_daily_loss_pct:
            self.logger.warning(f"Daily loss limit reached: {current_pnl:.2f}%")
            return False
        return True
    
    def check_drawdown(self, equity: float) -> bool:
        """
        Check if maximum drawdown is reached.
        
        Args:
            equity: Current equity value
            
        Returns:
            True if trading is allowed, False if limit reached
        """
        self.current_equity = equity
        
        if self.peak_equity == 0:
            self.peak_equity = equity
            return True
            
        if equity > self.peak_equity:
            self.peak_equity = equity
            
        drawdown = (self.peak_equity - equity) / self.peak_equity * 100
        
        if drawdown >= self.max_drawdown_pct:
            self.logger.warning(f"Max drawdown reached: {drawdown:.2f}%")
            return False
            
        return True
    
    def validate_trade(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a trade meets risk requirements.
        
        Args:
            account_balance: Current account balance
            entry_price: Proposed entry price
            stop_loss: Proposed stop loss
            
        Returns:
            (is_valid, reason_if_invalid)
        """
        # Check position size
        risk_amount = account_balance * (self.risk_per_trade_pct / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return False, "Invalid stop loss (same as entry)"
        
        # Check minimum reward:risk
        potential_reward = price_risk * self.reward_risk_ratio
        if potential_reward < price_risk * 1.5:
            return False, "Insufficient reward:risk ratio"
        
        return True, None
