"""
Alpaca Broker Integration
Live trading with Alpaca API
"""

import logging
import os
from datetime import datetime
from typing import Optional

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class AlpacaBroker:
    """Alpaca broker for live futures trading."""
    
    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        paper: bool = True,
        initial_balance: float = 100000
    ):
        self.logger = logging.getLogger(__name__)
        
        if not ALPACA_AVAILABLE:
            self.logger.error("Alpaca trade API not installed. Run: pip install alpaca-trade-api")
            return
            
        # Get API credentials from env or params
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            self.logger.error("Alpaca API key/secret not provided")
            return
        
        # Set endpoint
        if paper:
            self.base_url = 'https://paper-api.alpaca.markets'
        else:
            self.base_url = 'https://live-api.alpaca.markets'
        
        try:
            self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url, api_version='v2')
            self.logger.info(f"Connected to Alpaca ({'paper' if paper else 'live'})")
        except Exception as e:
            self.logger.error(f"Failed to connect to Alpaca: {e}")
            return
        
        self.paper = paper
        self.symbol = 'NQ'  # Nasdaq futures
        
    def get_account(self) -> dict:
        """Get account info."""
        try:
            account = self.api.get_account()
            return {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            self.logger.error(f"Error getting account: {e}")
            return {}
    
    def get_position(self) -> dict:
        """Get current position."""
        try:
            position = self.api.get_position(self.symbol)
            return {
                'size': int(position.qty),
                'avg_entry_price': float(position.avg_entry_price),
                'market_value': float(position.market_value),
                'unrealized_pl': float(position.unrealized_pl)
            }
        except Exception as e:
            # No position
            return {'size': 0}
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price."""
        try:
            bar = self.api.get_latest_bar(self.symbol)
            return float(bar.c)
        except Exception as e:
            self.logger.error(f"Error getting price: {e}")
            return None
    
    def submit_order(
        self,
        action: str,
        quantity: int = 1,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Optional[dict]:
        """Submit a trade order."""
        try:
            side = 'buy' if action == 'buy' else 'sell'
            
            # Submit order
            order = self.api.submit_order(
                symbol=self.symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            self.logger.info(f"Order submitted: {order.id} - {side} {quantity} {self.symbol}")
            
            # Add stop loss and take profit as bracket orders if provided
            # For simplicity, we'll manage exits separately
            
            return {
                'order_id': order.id,
                'status': order.status,
                'side': side,
                'qty': quantity
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return None
    
    def close_position(self, reason: str = 'signal') -> Optional[dict]:
        """Close current position."""
        try:
            position = self.get_position()
            if position['size'] == 0:
                return None
            
            order = self.api.close_position(self.symbol)
            
            self.logger.info(f"Position closed: {reason} - Order: {order.id}")
            
            return {
                'order_id': order.id,
                'status': order.status
            }
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def cancel_orders(self):
        """Cancel all open orders."""
        try:
            self.api.cancel_all_orders()
            self.logger.info("All orders cancelled")
        except Exception as e:
            self.logger.error(f"Error cancelling orders: {e}")


def create_alpaca_broker(paper: bool = True) -> AlpacaBroker:
    """Create Alpaca broker from environment variables."""
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("ERROR: Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        print("Get keys at: https://app.alpaca.markets/paper/dashboard/overview")
        return None
    
    return AlpacaBroker(api_key, secret_key, paper=paper)
