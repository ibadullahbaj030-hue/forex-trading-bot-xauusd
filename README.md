# XAUUSD Forex Trading Bot

An automated trading bot for XAUUSD (Gold/USD) using MetaTrader 5 with an EMA 20/50 moving average crossover strategy.

## Features

✅ **EMA 20/50 Crossover Strategy** - Automated signal generation based on exponential moving averages  
✅ **Risk Management** - 2% risk per trade with stop-loss and take-profit calculation  
✅ **Position Sizing** - Dynamic lot size calculation based on account balance and risk  
✅ **Multiple Trading Modes** - Demo, live, and backtest modes  
✅ **Backtesting** - Historical performance analysis with detailed statistics  
✅ **Logging & Monitoring** - Comprehensive logging for all trading activities  
✅ **Emergency Stop** - Safety mechanisms to protect against excessive losses  

## Requirements

- Python 3.8+
- MetaTrader 5 terminal installed and running
- Exness account (demo or live)
- Libraries: `MetaTrader5`, `pandas`, `numpy`

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ibadullahbaj030-hue/forex-trading-bot-xauusd.git
   cd forex-trading-bot-xauusd
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MetaTrader 5:**
   - Download and install [MetaTrader 5](https://www.metatrader5.com/)
   - Create/login to your Exness account in MT5
   - Keep MT5 running while the bot is active

4. **Configure the bot:**
   - Copy `.env.example` to `.env`
   - Fill in your Exness account details (optional if already logged in MT5)
   - Edit `config.py` to adjust trading parameters

## Configuration

Edit `config.py` to customize trading parameters:

```python
# Trading Symbol and Timeframe
SYMBOL = "XAUUSD"           # Gold/USD pair
TIMEFRAME = 1               # 1-minute timeframe

# Moving Average Strategy
FAST_EMA_PERIOD = 20        # Fast EMA period
SLOW_EMA_PERIOD = 50        # Slow EMA period

# Risk Management
RISK_PERCENT = 2.0          # Risk 2% per trade
MAX_STOP_LOSS_PIPS = 50     # Max stop loss in pips
TAKE_PROFIT_RATIO = 2.0     # Risk-to-reward ratio (TP = SL * ratio)

# Mode
DEMO_MODE = True            # ALWAYS use demo first!
BACKTEST_MODE = False       # Enable for backtesting
```

## Usage

### Run Live Trading (Demo Mode)

```bash
python trading_bot.py
```

**⚠️ IMPORTANT:** Always test on a demo account first before trading real money.

### Run Backtesting

1. Enable backtest mode in `config.py`:
   ```python
   BACKTEST_MODE = True
   DEMO_MODE = False
   ```

2. Run the backtester:
   ```bash
   python backtester.py
   ```

## Trading Strategy

### EMA Crossover Logic

- **BUY Signal**: When the 20-period EMA crosses above the 50-period EMA
- **SELL Signal**: When the 20-period EMA crosses below the 50-period EMA
- **Exit**: Stop-loss or take-profit levels are hit

### Risk Management

- **Position Size**: Calculated dynamically based on account balance and 2% risk per trade
- **Stop Loss**: 50 pips maximum
- **Take Profit**: Risk-to-reward ratio of 2:1 (TP = 100 pips for 50-pip SL)
- **Max Open Positions**: 1 position per symbol
- **Daily Loss Limit**: 5% of account balance

## File Structure

```
├── config.py              # Trading configuration and parameters
├── trading_bot.py         # Main trading bot with EMA strategy
├── backtester.py          # Backtesting module
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── trading_bot.log        # Trading activity logs
└── README.md              # This file
```

## Logs

All trading activities are logged to `trading_bot.log` and console output.

Example log output:
```
2024-09-30 10:15:23 - __main__ - INFO - Connected to MT5
2024-09-30 10:15:24 - __main__ - INFO - Signal generated: BUY
2024-09-30 10:15:25 - __main__ - INFO - Order placed: BUY 0.10 XAUUSD @ 2350.50
2024-09-30 10:25:30 - __main__ - INFO - TP @ 2375.00 | PnL: +$250.00
```

## Safety Considerations

1. **Start with demo account** - Never start with real money
2. **Backtest first** - Always backtest the strategy before live trading
3. **Monitor the bot** - Don't leave it unattended for long periods
4. **Set emergency stop** - Configure `EMERGENCY_STOP` in config if needed
5. **Verify MT5** - Ensure MetaTrader 5 is running and logged in
6. **Check connectivity** - Confirm the bot can connect to your account

## Common Issues

### "Failed to connect to MT5"
- Ensure MetaTrader 5 is installed and running
- Verify your Exness account is logged in MT5
- Check that the server name in `config.py` matches your account type

### "No rates retrieved"
- Confirm the symbol XAUUSD is available on your account
- Check symbol spelling in `config.py`

### "Order failed"
- Verify you have sufficient margin/balance
- Check that the symbol allows trading at this time
- Ensure SL/TP prices are valid

## Trading Risk Disclaimer

⚠️ **Forex trading carries significant risk.** This bot is for educational purposes. 

- You can lose your entire investment
- Past performance does not guarantee future results
- Always use stop-loss and risk management
- Start with small account sizes and demo trading
- Never trade with money you cannot afford to lose

## Future Enhancements

- [ ] Additional indicators (RSI, MACD, Bollinger Bands)
- [ ] Machine learning-based signal generation
- [ ] Database logging for trade history
- [ ] Web dashboard for monitoring
- [ ] Alert notifications (Email, Discord, Telegram)
- [ ] Multi-symbol trading support
- [ ] Advanced risk management strategies

## Support

For issues or questions, please open a GitHub issue.

## License

MIT License - See LICENSE file for details

## Disclaimer

This bot is provided for educational and research purposes only. The author is not responsible for any financial losses. Use at your own risk.
