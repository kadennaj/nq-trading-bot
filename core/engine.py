"""
Trading Engine Core
Orchestrates data fetching, strategy signals, and trade execution
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from execution.broker import Broker
from strategies.swing_strategy import SwingStrategy


class TradingEngine:
    """Main trading engine that coordinates all components."""
    
    def __init__(
        self,
        data_fetcher,
        broker: Broker,
        strategy: SwingStrategy,
        symbol: str = 'NQ',
        mode: str = 'paper',
        check_interval: int = 15,
        alert_manager=None
    ):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = data_fetcher
        self.broker = broker
        self.strategy = strategy
        self.symbol = symbol
        self.mode = mode
        self.check_interval = check_interval
        self.alert_manager = alert_manager
        
        # Track trades for stats
        self.trades = []
        self.daily_trades = {}
        
    def run_live(self):
        """Run in paper or live trading mode."""
        self.logger.info(f"Starting live trading mode: {self.mode}")
        self.logger.info(f"Check interval: {self.check_interval} minutes")
        
        while True:
            try:
                self._check_and_trade()
                time.sleep(self.check_interval * 60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}", exc_info=True)
                time.sleep(60)
    
    def _check_and_trade(self):
        """Check for trading signals and execute if valid."""
        # Fetch latest data
        df = self.data_fetcher.fetch_recent_data()
        
        if df is None or df.empty:
            self.logger.warning("No data available, skipping cycle")
            return
        
        # Get strategy signal
        signal = self.strategy.get_signal(df)
        
        if signal:
            self.logger.info(f"Signal generated: {signal}")
            self._execute_trade(signal, df)
        else:
            self.logger.debug("No signal this cycle")
    
    def _execute_trade(self, signal: dict, df: pd.DataFrame):
        """Execute a trade based on the signal."""
        action = signal['action']
        entry_price = signal.get('entry_price', df['close'].iloc[-1])
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        # Check if we already have a position
        position = self.broker.get_position()
        
        if position and position['size'] != 0:
            self.logger.info(f"Already in position: {position['size']} {self.symbol}")
            return
        
        # Check daily trade limit (0.5 trades/day = ~1 trade every 2 days)
        today = datetime.now().date()
        trades_today = self.daily_trades.get(today, 0)
        
        if trades_today >= 1:
            self.logger.info("Daily trade limit reached (0.5 trades/day target)")
            return
        
        # Execute trade
        if self.mode == 'live':
            result = self.broker.execute(action, entry_price, stop_loss, take_profit)
        else:
            result = self.broker.paper_trade(action, entry_price, stop_loss, take_profit)
        
        if result:
            self.trades.append({
                'timestamp': datetime.now(),
                'action': action,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'mode': self.mode
            })
            self.daily_trades[today] = trades_today + 1
            self.logger.info(f"Trade executed: {action} {self.symbol} @ {entry_price}")
            
            # Send alert
            if self.alert_manager:
                signal['entry_price'] = entry_price
                self.alert_manager.send_trade_signal(signal, entry_price)
    
    def run_backtest(self, start_date: str, end_date: str):
        """Run backtesting mode."""
        self.logger.info(f"Running backtest: {start_date} to {end_date}")
        
        # Fetch historical data
        df = self.data_fetcher.fetch_historical(start_date, end_date)
        
        if df is None or df.empty:
            self.logger.error("No historical data available")
            return
        
        self.logger.info(f"Loaded {len(df)} bars for backtesting")
        
        # Generate signals for each bar
        signals = []
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(100, len(df)):  # Need warmup for indicators
            df_slice = df.iloc[:i+1]
            signal = self.strategy.get_signal(df_slice)
            
            if signal and position == 0:
                # Enter trade
                position = 1 if signal['action'] == 'buy' else -1
                entry_price = df['close'].iloc[i]
                stop_loss = signal.get('stop_loss')
                take_profit = signal.get('take_profit')
                
                trades.append({
                    'entry_time': df.index[i],
                    'entry_price': entry_price,
                    'action': signal['action'],
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                })
                self.logger.info(f"BACKTEST: {signal['action'].upper()} @ {entry_price:.2f}")
            
            elif position != 0:
                # Check exit conditions
                current_price = df['close'].iloc[i]
                
                # Stop loss hit
                if position == 1 and stop_loss and current_price <= stop_loss:
                    pnl = current_price - entry_price
                    self.logger.info(f"BACKTEST: STOP LOSS | PnL: {pnl:.2f}")
                    position = 0
                    trades[-1].update({
                        'exit_time': df.index[i],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'exit_reason': 'stop_loss'
                    })
                elif position == -1 and stop_loss and current_price >= stop_loss:
                    pnl = entry_price - current_price
                    self.logger.info(f"BACKTEST: STOP LOSS | PnL: {pnl:.2f}")
                    position = 0
                    trades[-1].update({
                        'exit_time': df.index[i],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'exit_reason': 'stop_loss'
                    })
                
                # Take profit hit
                elif position == 1 and take_profit and current_price >= take_profit:
                    pnl = current_price - entry_price
                    self.logger.info(f"BACKTEST: TAKE PROFIT | PnL: {pnl:.2f}")
                    position = 0
                    trades[-1].update({
                        'exit_time': df.index[i],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'exit_reason': 'take_profit'
                    })
                elif position == -1 and take_profit and current_price <= take_profit:
                    pnl = entry_price - current_price
                    self.logger.info(f"BACKTEST: TAKE PROFIT | PnL: {pnl:.2f}")
                    position = 0
                    trades[-1].update({
                        'exit_time': df.index[i],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'exit_reason': 'take_profit'
                    })
        
        # Calculate stats
        self._print_backtest_stats(trades, df)
    
    def _print_backtest_stats(self, trades, df: pd.DataFrame):
        """Print backtesting statistics."""
        if not trades:
            self.logger.info("No trades executed during backtest")
            return
        
        closed_trades = [t for t in trades if 'pnl' in t]
        
        if not closed_trades:
            self.logger.info("No closed trades to analyze")
            return
        
        wins = [t for t in closed_trades if t['pnl'] > 0]
        losses = [t for t in closed_trades if t['pnl'] <= 0]
        
        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        total_pnl = sum(t['pnl'] for t in closed_trades)
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        
        # Calculate max drawdown
        cumulative = 0
        max_dd = 0
        peak = 0
        for t in closed_trades:
            cumulative += t['pnl']
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        # Days in backtest
        days = (df.index[-1] - df.index[0]).days
        trades_per_day = len(closed_trades) / days if days > 0 else 0
        
        self.logger.info("=" * 50)
        self.logger.info("BACKTEST RESULTS")
        self.logger.info("=" * 50)
        self.logger.info(f"Total trades: {len(closed_trades)}")
        self.logger.info(f"Wins: {len(wins)} | Losses: {len(losses)}")
        self.logger.info(f"Win rate: {win_rate:.1f}%")
        self.logger.info(f"Total PnL: {total_pnl:.2f} points")
        self.logger.info(f"Avg win: {avg_win:.2f} | Avg loss: {avg_loss:.2f}")
        self.logger.info(f"Max drawdown: {max_dd:.2f} points")
        self.logger.info(f"Trades/day: {trades_per_day:.2f}")
        self.logger.info("=" * 50)
