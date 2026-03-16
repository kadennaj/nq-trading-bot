# NQ Trading Bot

Quantitative trading engine for Nasdaq futures (NQ) with a focus on high win rate and low drawdown.

## Strategy Overview

The swing strategy is designed for **~0.5 trades per day** (approximately 1 trade every 2 days) through:

- **Multi-timeframe analysis**: 4H charts with daily trend confirmation
- **Trend alignment**: Only trade in direction of EMA 200 (both timeframes)
- **Mean reversion**: Enter on pullbacks to Bollinger Bands
- **RSI signals**: Oversold (35) for longs, overbought (65) for shorts
- **ATR-based stops**: Adaptive to market volatility
- **3:1 reward:risk ratio**: Target 3x the stop loss distance

## Installation

```bash
# Clone the repo
git clone https://github.com/kadennaj/nq-trading-bot.git
cd nq-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Paper Trading (Live)

```bash
python main.py --mode paper --symbol NQ
```

### Backtesting

```bash
python main.py --mode backtest --start-date 2023-01-01 --end-date 2024-01-01
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--symbol` | Futures symbol | NQ |
| `--mode` | Trading mode | paper |
| `--interval` | Check interval (min) | 15 |
| `-v` | Verbose output | false |

## Project Structure

```
nq-trading-bot/
├── main.py                 # Entry point
├── core/
│   ├── engine.py          # Trading engine
│   └── risk_manager.py    # Risk management
├── strategies/
│   └── swing_strategy.py  # Swing trading strategy
├── data/
│   └── fetcher.py         # Market data fetching
├── execution/
│   └── broker.py          # Trade execution
└── requirements.txt       # Dependencies
```

## Strategy Parameters

- **EMA Period**: 200 (trend), 50 (momentum)
- **RSI Period**: 14
- **RSI Levels**: 35 (oversold), 65 (overbought)
- **Bollinger Bands**: 20 period, 2 std
- **ATR Stop**: 1.5x ATR
- **Take Profit**: 3.0x ATR
- **Max Daily Trades**: 1 (to achieve ~0.5/day average)

## Risk Management

- **Risk per trade**: 0.5% of account
- **Max daily loss**: 3%
- **Max drawdown**: 10%
- **Position sizing**: ATR-based

## To Do

- [ ] Add broker integrations (Alpaca, IB, TrendFutures)
- [ ] Add Telegram notifications
- [ ] Add position trailing stops
- [ ] Add more sophisticated trend detection
- [ ] Add backtest visualization

## Disclaimer

This software is for educational purposes. Futures trading involves substantial risk. Always use proper risk management and test thoroughly before trading with real money.
