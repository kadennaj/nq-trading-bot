"""
Swing Strategy for NQ Futures
EMA Trend Strategy with multiple entry types
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np


class SwingStrategy:
    """
    EMA Trend Strategy - Multiple confirmation for quality trades
    """
    
    def __init__(self, symbol: str = 'NQ'):
        self.logger = logging.getLogger(__name__)
        self.symbol = symbol
        
        # Strategy parameters
        self.ema_fast = 9
        self.ema_slow = 21
        self.atr_period = 14
        self.atr_stop_multiplier = 1.5
        self.atr_tp_multiplier = 3.0  # 2:1
        
    def get_signal(self, df: pd.DataFrame) -> Optional[dict]:
        """Generate trading signal."""
        if df is None or len(df) < 50:
            return None
            
        df = self._calculate_indicators(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None
        
        if prev is None:
            return None
        
        # Determine trend
        ema_trend = 'bullish' if latest['ema_9'] > latest['ema_21'] else 'bearish'
        
        # Check for long entries
        if ema_trend == 'bullish':
            signal = self._check_long(df, latest, prev)
            if signal:
                return signal
        
        # Check for short entries
        if ema_trend == 'bearish':
            signal = self._check_short(df, latest, prev)
            if signal:
                return signal
        
        return None
    
    def _check_long(self, df, latest, prev) -> Optional[dict]:
        """Check for long entry."""
        
        close = latest['close']
        prev_close = prev['close']
        atr = latest['atr']
        
        # Entry type 1: Pullback to EMA 9 (most common)
        # Price pulled back to EMA 9 and bouncing
        if close >= latest['ema_9']:
            return None
            
        if prev_close >= prev['ema_9']:
            return None
        
        # Must be bullish candle
        if close <= prev_close:
            return None
        
        # Close in upper portion of range
        range_size = latest['high'] - latest['low']
        if range_size > 0:
            position = (close - latest['low']) / range_size
            if position < 0.5:
                return None
        
        stop_loss = close - (atr * self.atr_stop_multiplier)
        take_profit = close + (atr * self.atr_tp_multiplier)
        
        return {
            'action': 'buy',
            'entry_price': close,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': 'ema_pullback_long',
            'atr': atr
        }
    
    def _check_short(self, df, latest, prev) -> Optional[dict]:
        """Check for short entry."""
        
        close = latest['close']
        prev_close = prev['close']
        atr = latest['atr']
        
        # Entry: Pullback to EMA 9
        if close <= latest['ema_9']:
            return None
            
        if prev_close <= prev['ema_9']:
            return None
        
        # Must be bearish candle
        if close >= prev_close:
            return None
        
        # Close in lower portion of range
        range_size = latest['high'] - latest['low']
        if range_size > 0:
            position = (close - latest['low']) / range_size
            if position > 0.5:
                return None
        
        stop_loss = close + (atr * self.atr_stop_multiplier)
        take_profit = close - (atr * self.atr_tp_multiplier)
        
        return {
            'action': 'sell',
            'entry_price': close,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': 'ema_pullback_short',
            'atr': atr
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators."""
        df = df.copy()
        
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()
        
        return df
    
    def get_strategy_info(self) -> dict:
        """Return strategy info."""
        return {
            'name': 'EMA Pullback Strategy',
            'expected_trades_per_day': 0.5,
            'target_win_rate': 55,
            'reward_risk': '2:1'
        }
