#!/usr/bin/env python3
"""
Configuration file for the XAUUSD trading bot.
All trading parameters and settings are defined here.
"""

# MetaTrader 5 Configuration
MT5_PATH = None  # Auto-detect MT5 installation. Set to explicit path if needed.
ACCOUNT_NUMBER = None  # Set to your Exness account number (DEMO account recommended)
ACCOUNT_PASSWORD = None  # Set to your account password
SERVER = "ExnessMT5Real"  # Change to "ExnessMT5Demo" for demo account

# Trading Symbol and Timeframe
SYMBOL = "XAUUSD"
TIMEFRAME = 1  # 1 = 1-minute (M1)

# Moving Average Strategy
FAST_EMA_PERIOD = 20  # Fast EMA period
SLOW_EMA_PERIOD = 50  # Slow EMA period

# Risk Management
RISK_PERCENT = 2.0  # Risk 2% of account balance per trade
MAX_STOP_LOSS_PIPS = 50  # Maximum stop loss in pips
TAKE_PROFIT_RATIO = 2.0  # Risk-to-reward ratio (TP = SL * ratio)
MAX_OPEN_POSITIONS = 1  # Maximum number of open positions per symbol

# Trading Hours (24-hour format, in UTC)
TRADING_START_HOUR = 0  # Start trading
TRADING_END_HOUR = 23  # Stop trading (set to None to trade 24/7)

# Logging Configuration
LOG_FILE = "trading_bot.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Mode Configuration
DEMO_MODE = True  # Set to False for live trading (NOT RECOMMENDED until fully tested)
BACKTEST_MODE = False  # Set to True to run backtests instead of live trading

# Backtest Configuration
BACKTEST_START_DATE = "2024-01-01"
BACKTEST_END_DATE = "2024-09-30"
BACKTEST_INITIAL_BALANCE = 10000  # Initial account balance for backtest

# Emergency Stop
EMERGENCY_STOP = False  # Set to True to stop the bot immediately
MAX_DAILY_LOSS_PERCENT = 5.0  # Stop trading if daily loss exceeds this %
