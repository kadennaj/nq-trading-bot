#!/usr/bin/env python3
"""
NQ Futures Trading Engine
Quantitative trading bot for Nasdaq futures (NQ)
Designed for ~0.5 trades/day with high win rate and low drawdown
"""

import argparse
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

from core.engine import TradingEngine
from data.fetcher import DataFetcher
from execution.broker import Broker
from execution.alpaca_broker import create_alpaca_broker
from strategies.swing_strategy import SwingStrategy


def setup_logging(verbose: bool = False):
    """Configure logging for the trading engine."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def signal_handler(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM."""
    logging.info("Shutdown signal received, closing positions...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='NQ Futures Trading Engine')
    parser.add_argument('--symbol', default='NQ', help='Futures symbol (default: NQ)')
    parser.add_argument('--mode', choices=['backtest', 'paper', 'live'], default='paper',
                        help='Trading mode (default: paper)')
    parser.add_argument('--broker', choices=['paper', 'alpaca', 'ibkr', 'rithmic'], default='paper',
                        help='Broker to use (default: paper)')
    parser.add_argument('--strategy', default='swing', help='Strategy to use (default: swing)')
    parser.add_argument('--interval', type=int, default=15, 
                        help='Check interval in minutes (default: 15)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--start-date', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Backtest end date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting NQ Trading Engine | Symbol: {args.symbol} | Mode: {args.mode}")
    
    # Initialize components
    data_fetcher = DataFetcher(symbol=args.symbol)
    
    # Initialize broker
    if args.broker == 'alpaca':
        from execution.alpaca_broker import create_alpaca_broker
        broker = create_alpaca_broker(paper=(args.mode == 'paper'), symbol=args.symbol)
    elif args.broker == 'ibkr':
        from execution.ibkr_broker import create_ibkr_broker
        broker = create_ibkr_broker(paper=(args.mode == 'paper'))
    elif args.broker == 'rithmic':
        from execution.rithmic_broker import create_rithmic_broker
        broker = create_rithmic_broker(paper=(args.mode == 'paper'), symbol=args.symbol)
    else:
        broker = Broker(mode=args.mode, symbol=args.symbol)
    
    strategy = SwingStrategy(symbol=args.symbol)
    
    # Initialize trading engine
    engine = TradingEngine(
        data_fetcher=data_fetcher,
        broker=broker,
        strategy=strategy,
        symbol=args.symbol,
        mode=args.mode,
        check_interval=args.interval
    )
    
    if args.mode == 'backtest':
        if not args.start_date or not args.end_date:
            logger.error("Backtest mode requires --start-date and --end-date")
            sys.exit(1)
        engine.run_backtest(args.start_date, args.end_date)
    else:
        # Paper or live trading
        logger.info("Starting live trading loop...")
        logger.info(f"Check interval: {args.interval} minutes")
        
        # Show account info for Alpaca
        if args.broker == 'alpaca':
            account = broker.get_account()
            logger.info(f"Account: ${account.get('portfolio_value', 0):.2f}")
        
        engine.run_live()


if __name__ == '__main__':
    main()
