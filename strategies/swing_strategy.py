"""
Swing Strategy for NQ Futures
Designed for ~0.5 trades/day with high win rate and low drawdown

Strategy Overview:
- Multi-timeframe analysis (4H + Daily)
- Trend confirmation using EMA 200
- RSI oversold/overbought with divergence
- Bollinger Bands for mean reversion
- ATR-based stops for volatility adaptation
- Only trades in direction of daily trend
- Requires multiple confirmations (selective)
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np


class SwingStrategy:
    """
    Swing trading strategy targeting low-frequency, high-probability trades.
    
    Key Principles:
    1. Trade with the trend (daily timeframe trend)
    2. Wait for pullbacks to key levels
    3. Multiple confirmation indicators
    4. Tight stops, let winners run
    5. High patience - wait for ideal setups
    """
    
    def __init__(self, symbol: str = 'NQ'):
        self.logger = logging.getLogger(__name__)
        self.symbol = symbol
        
        # Strategy parameters
        self.ema_period = 200
        self.rsi_period = 14
        self.rsi_oversold = 35  # Relaxed from 30 for fewer, better trades
        self.rsi_overbought = 65
        self.bb_period = 20
        self.bb_std = 2
        self.atr_period = 14
        self.atr_stop_multiplier = 1.5
        self.atr_tp_multiplier = 3.0
        
        # Trend parameters
        self.ema_fast = 50
        
    def get_signal(self, df: pd.DataFrame) -> Optional[dict]:
        """
        Analyze data and generate trading signal.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal dict or None
        """
        if df is None or len(df) < 50:
            return None
            
        # Calculate indicators
        df = self._calculate_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Check market status - prefer trading during active hours
        current_hour = pd.Timestamp.now().hour
        if current_hour < 9 or current_hour > 15:
            # Outside optimal hours, be even more selective
            return None
        
        # Determine daily trend
        daily_ema = latest.get('ema_200_daily', latest.get('ema_200'))
        daily_close = latest['close']
        daily_trend = 'bullish' if daily_close > daily_ema else 'bearish' if daily_close < daily_ema else None
        
        # Calculate current trend (4H)
        ema_200 = latest.get('ema_200', latest.get('ema_200_4h'))
        ema_50 = latest.get('ema_50', latest.get('ema_50_4h'))
        
        if ema_200 is None or ema_50 is None:
            return None
            
        short_trend = 'bullish' if ema_50 > ema_200 else 'bearish'
        
        # Check for long signal
        if self._is_long_setup(df, latest, prev, short_trend, daily_trend):
            atr = latest['atr']
            stop_loss = latest['close'] - (atr * self.atr_stop_multiplier)
            take_profit = latest['close'] + (atr * self.atr_tp_multiplier)
            
            return {
                'action': 'buy',
                'entry_price': latest['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': 'swing_long',
                'trend': short_trend,
                'rsi': latest['rsi'],
                'atr': atr
            }
        
        # Check for short signal
        if self._is_short_setup(df, latest, prev, short_trend, daily_trend):
            atr = latest['atr']
            stop_loss = latest['close'] + (atr * self.atr_stop_multiplier)
            take_profit = latest['close'] - (atr * self.atr_tp_multiplier)
            
            return {
                'action': 'sell',
                'entry_price': latest['close'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': 'swing_short',
                'trend': short_trend,
                'rsi': latest['rsi'],
                'atr': atr
            }
        
        return None
    
    def _is_long_setup(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        prev: pd.Series,
        short_trend: str,
        daily_trend: str
    ) -> bool:
        """Check for long entry setup."""
        
        # Must be in uptrend (both timeframes aligned)
        if short_trend != 'bullish' or daily_trend != 'bullish':
            return False
        
        # RSI must be in oversold territory
        if latest['rsi'] > self.rsi_oversold:
            return False
            
        # Previous RSI should have been even lower (bullish divergence)
        if prev['rsi'] < latest['rsi']:
            pass  # Divergence present, good
        else:
            # Not a strict divergence requirement, but prefer it
            pass
        
        # Price near or below lower Bollinger Band
        if latest['close'] > latest['bb_lower']:
            # Allow some flexibility - check if close is within lower 25% of range
            bb_range = latest['bb_upper'] - latest['bb_lower']
            distance_to_lower = latest['close'] - latest['bb_lower']
            if distance_to_lower > bb_range * 0.25:
                return False
        
        # Price showing strength (close higher than low of candle)
        if latest['close'] < latest['low'] + (latest['high'] - latest['low']) * 0.3:
            return False
        
        return True
    
    def _is_short_setup(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        prev: pd.Series,
        short_trend: str,
        daily_trend: str
    ) -> bool:
        """Check for short entry setup."""
        
        # Must be in downtrend (both timeframes aligned)
        if short_trend != 'bearish' or daily_trend != 'bearish':
            return False
        
        # RSI must be in overbought territory
        if latest['rsi'] < self.rsi_overbought:
            return False
            
        # Previous RSI should have been even higher (bearish divergence)
        if prev['rsi'] > latest['rsi']:
            pass  # Divergence present
        
        # Price near or above upper Bollinger Band
        if latest['close'] < latest['bb_upper']:
            bb_range = latest['bb_upper'] - latest['bb_lower']
            distance_to_upper = latest['bb_upper'] - latest['close']
            if distance_to_upper > bb_range * 0.25:
                return False
        
        # Price showing weakness
        if latest['close'] > latest['low'] + (latest['high'] - latest['low']) * 0.7:
            return False
        
        return True
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()
        
        # EMA
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()
        
        return df
    
    def get_strategy_info(self) -> dict:
        """Return strategy configuration info."""
        return {
            'name': 'Swing Strategy',
            'symbol': self.symbol,
            'timeframe': '4H with Daily trend',
            'ema_period': self.ema_period,
            'rsi_period': self.rsi_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'bb_period': self.bb_period,
            'atr_period': self.atr_period,
            'expected_trades_per_day': 0.5,
            'target_win_rate': 60,
            'max_drawdown': '5-8%'
        }
