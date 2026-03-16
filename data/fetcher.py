"""
Data Fetcher
Fetches futures data from various sources
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf


class DataFetcher:
    """Fetches market data for futures trading."""
    
    def __init__(self, symbol: str = 'NQ', data_source: str = 'yahoo'):
        self.logger = logging.getLogger(__name__)
        self.symbol = symbol
        self.data_source = data_source
        
        # Yahoo Finance uses different ticker format for futures
        self.ticker = self._get_ticker(symbol)
        
    def _get_ticker(self, symbol: str) -> str:
        """Map symbol to Yahoo Finance ticker."""
        # NQ = Nasdaq 100 Futures - use futures format
        ticker_map = {
            'NQ': 'NQ=F',  # Yahoo Finance futures format
            'ES': 'ES=F',  # S&P 500 Futures
            'YM': 'YM=F',  # Dow Jones Futures
            'RTY': 'RTY=F', # Russell 2000 Futures
        }
        return ticker_map.get(symbol, symbol)
    
    def fetch_recent_data(
        self,
        timeframe: str = '1h',
        periods: int = 200
    ) -> Optional[pd.DataFrame]:
        """
        Fetch recent market data.
        
        Args:
            timeframe: Data timeframe (1m, 5m, 15m, 1h, 1d)
            periods: Number of periods to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(self.ticker)
            df = ticker.history(period=f'{periods}{self._timeframe_to_yahoo(timeframe)}')
            
            if df.empty:
                self.logger.warning(f"No data returned for {self.ticker}")
                return None
            
            df = self._normalize_columns(df)
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}")
            return None
    
    def fetch_historical(
        self,
        start_date: str,
        end_date: str,
        timeframe: str = '1h'
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for backtesting.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(self.ticker)
            df = ticker.history(start=start_date, end=end_date, interval=self._timeframe_to_yahoo(timeframe))
            
            if df.empty:
                self.logger.warning(f"No historical data for {self.ticker}")
                return None
            
            df = self._normalize_columns(df)
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return None
    
    def _timeframe_to_yahoo(self, timeframe: str) -> str:
        """Convert timeframe to Yahoo Finance format."""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1wk',
        }
        return mapping.get(timeframe, '1h')
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase."""
        df.columns = [c.lower() for c in df.columns]
        
        # Ensure required columns exist
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                self.logger.warning(f"Missing column: {col}")
                
        return df
    
    def get_current_price(self) -> Optional[float]:
        """Get the current market price."""
        df = self.fetch_recent_data(periods=1)
        if df is not None and not df.empty:
            return df['close'].iloc[-1]
        return None
    
    def get_market_status(self) -> dict:
        """Get current market status (open/closed, hours, etc.)."""
        now = datetime.now()
        
        # NYSE hours (EST)
        market_open = now.replace(hour=9, minute=30, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        
        # Check if weekend
        is_weekend = now.weekday() >= 5
        is_market_hours = market_open <= now <= market_close and not is_weekend
        
        return {
            'timestamp': now,
            'is_open': is_market_hours,
            'is_weekend': is_weekend,
            'market_open': market_open,
            'market_close': market_close
        }
