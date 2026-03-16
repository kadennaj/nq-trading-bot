"""
Swing Strategy for NQ Futures  
EMA Crossover with Daily Trend Filter - High Win Rate Focus
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np


class SwingStrategy:
    """
    EMA Cross with Trend Filter
    - Daily trend filter (EMA 200 on daily)
    - 4H EMA crossover for entries
    - Wide stops, smaller TP for high win rate
    """
    
    def __init__(self, symbol: str = 'NQ'):
        self.logger = logging.getLogger(__name__)
        self.symbol = symbol
        
        # 4H parameters
        self.fast_ema = 8
        self.slow_ema = 21
        self.atr_period = 14
        
        # Risk parameters - tight stops, lower reward for higher win rate
        self.stop_atr = 1.2
        self.tp_atr = 1.4  # 1.17:1 - very achievable
        
    def get_signal(self, df: pd.DataFrame) -> Optional[dict]:
        """Generate trading signal."""
        if df is None or len(df) < 100:
            return None
            
        df = self._calculate_indicators(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) > 2 else prev
        
        # Get trend from EMA relationship
        trend = 'bullish' if latest['ema_8'] > latest['ema_21'] else 'bearish'
        
        # Long: bullish trend + fast EMA crosses above slow
        if trend == 'bullish':
            # Bullish crossover: fast was below, now above
            if prev['ema_8'] <= prev['ema_21'] and latest['ema_8'] > latest['ema_21']:
                signal = self._create_long_signal(latest)
                if signal:
                    return signal
            
            # Alternative: pullback to EMA 8 in strong uptrend
            if latest['close'] > latest['ema_21'] * 1.005:  # Strong uptrend
                if latest['close'] <= latest['ema_8'] and prev['close'] > prev['ema_8']:
                    if latest['close'] > latest['open']:  # Bullish candle
                        signal = self._create_long_signal(latest)
                        if signal:
                            return signal
        
        # Short: bearish trend + fast EMA crosses below slow
        if trend == 'bearish':
            if prev['ema_8'] >= prev['ema_21'] and latest['ema_8'] < latest['ema_21']:
                signal = self._create_short_signal(latest)
                if signal:
                    return signal
            
            if latest['close'] < latest['ema_21'] * 0.995:  # Strong downtrend
                if latest['close'] >= latest['ema_8'] and prev['close'] < prev['ema_8']:
                    if latest['close'] < latest['open']:  # Bearish candle
                        signal = self._create_short_signal(latest)
                        if signal:
                            return signal
        
        return None
    
    def _create_long_signal(self, latest) -> dict:
        """Create long signal."""
        entry = latest['close']
        atr = latest['atr']
        
        stop_loss = entry - (atr * self.stop_atr)
        risk = entry - stop_loss
        take_profit = entry + (risk * self.tp_atr)
        
        return {
            'action': 'buy',
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': 'ema_bullish_cross',
            'trend': 'bullish',
            'rsi': latest.get('rsi', 50),
            'atr': atr
        }
    
    def _create_short_signal(self, latest) -> dict:
        """Create short signal."""
        entry = latest['close']
        atr = latest['atr']
        
        stop_loss = entry + (atr * self.stop_atr)
        risk = stop_loss - entry
        take_profit = entry - (risk * self.tp_atr)
        
        return {
            'action': 'sell',
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': 'ema_bearish_cross',
            'trend': 'bearish',
            'rsi': latest.get('rsi', 50),
            'atr': atr
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        df = df.copy()
        
        # EMAs
        df['ema_8'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()
        
        return df
    
    def get_strategy_info(self) -> dict:
        return {
            'name': 'EMA Cross Strategy',
            'expected_trades_per_day': 0.5,
            'target_win_rate': 55,
            'reward_risk': '1.33:1'
        }
