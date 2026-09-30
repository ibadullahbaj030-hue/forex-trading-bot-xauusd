#!/usr/bin/env python3
"""
Backtesting module for the XAUUSD trading bot.
Simulates historical trading to evaluate strategy performance.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from config import (
    SYMBOL, FAST_EMA_PERIOD, SLOW_EMA_PERIOD,
    RISK_PERCENT, MAX_STOP_LOSS_PIPS, TAKE_PROFIT_RATIO,
    BACKTEST_START_DATE, BACKTEST_END_DATE, BACKTEST_INITIAL_BALANCE,
    LOG_FILE, LOG_LEVEL, MT5_PATH
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Backtester:
    """Backtest the EMA crossover strategy."""

    def __init__(self, start_date, end_date, initial_balance):
        """Initialize backtester."""
        self.symbol = SYMBOL
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades = []
        self.open_position = None
        self.connected = False

    def connect_mt5(self):
        """Connect to MetaTrader 5."""
        try:
            if MT5_PATH:
                if not mt5.initialize(path=MT5_PATH):
                    logger.error(f"Failed to initialize MT5 with path: {MT5_PATH}")
                    return False
            else:
                if not mt5.initialize():
                    logger.error("Failed to initialize MT5")
                    return False

            self.connected = True
            logger.info("Connected to MT5 for backtesting")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False

    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5."""
        try:
            mt5.shutdown()
            self.connected = False
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")

    def get_historical_data(self):
        """Fetch historical OHLCV data."""
        try:
            # Convert dates to timestamp
            from_date = int(self.start_date.timestamp())
            to_date = int(self.end_date.timestamp())

            # Fetch 1-minute data
            rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, self.start_date, self.end_date)

            if rates is None or len(rates) == 0:
                logger.error(f"No historical data found for {self.symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            logger.info(f"Fetched {len(df)} candles from {df['time'].min()} to {df['time'].max()}")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None

    def calculate_ema(self, df, period):
        """Calculate Exponential Moving Average."""
        return df['close'].ewm(span=period, adjust=False).mean()

    def backtest(self):
        """Run the backtest."""
        if not self.connect_mt5():
            logger.error("Failed to connect to MT5")
            return

        try:
            # Get historical data
            df = self.get_historical_data()
            if df is None or len(df) < SLOW_EMA_PERIOD:
                logger.error("Insufficient data for backtest")
                return

            # Calculate EMAs
            df['ema_fast'] = self.calculate_ema(df, FAST_EMA_PERIOD)
            df['ema_slow'] = self.calculate_ema(df, SLOW_EMA_PERIOD)

            logger.info(f"Starting backtest from {df['time'].min()} to {df['time'].max()}")
            logger.info(f"Initial balance: ${self.initial_balance:.2f}")
            logger.info(f"Strategy: EMA {FAST_EMA_PERIOD}/{SLOW_EMA_PERIOD}")

            # Simulate trading
            for i in range(SLOW_EMA_PERIOD, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i - 1]

                # Check for BUY signal
                if previous['ema_fast'] <= previous['ema_slow'] and \
                   current['ema_fast'] > current['ema_slow'] and \
                   self.open_position is None:
                    self.open_position = {
                        'type': 'BUY',
                        'entry_price': current['close'],
                        'entry_time': current['time'],
                        'sl': current['close'] - (MAX_STOP_LOSS_PIPS * 0.0001),
                        'tp': current['close'] + (MAX_STOP_LOSS_PIPS * TAKE_PROFIT_RATIO * 0.0001)
                    }
                    logger.info(f"BUY @ {current['time']}: {self.open_position['entry_price']:.5f}")

                # Check for SELL signal
                elif previous['ema_fast'] >= previous['ema_slow'] and \
                     current['ema_fast'] < current['ema_slow'] and \
                     self.open_position is None:
                    self.open_position = {
                        'type': 'SELL',
                        'entry_price': current['close'],
                        'entry_time': current['time'],
                        'sl': current['close'] + (MAX_STOP_LOSS_PIPS * 0.0001),
                        'tp': current['close'] - (MAX_STOP_LOSS_PIPS * TAKE_PROFIT_RATIO * 0.0001)
                    }
                    logger.info(f"SELL @ {current['time']}: {self.open_position['entry_price']:.5f}")

                # Check for exit conditions (SL/TP)
                if self.open_position:
                    exit_price = None
                    exit_type = None

                    if self.open_position['type'] == 'BUY':
                        if current['low'] <= self.open_position['sl']:
                            exit_price = self.open_position['sl']
                            exit_type = 'SL'
                        elif current['high'] >= self.open_position['tp']:
                            exit_price = self.open_position['tp']
                            exit_type = 'TP'
                    else:  # SELL
                        if current['high'] >= self.open_position['sl']:
                            exit_price = self.open_position['sl']
                            exit_type = 'SL'
                        elif current['low'] <= self.open_position['tp']:
                            exit_price = self.open_position['tp']
                            exit_type = 'TP'

                    if exit_price:
                        # Calculate P&L
                        if self.open_position['type'] == 'BUY':
                            pnl = (exit_price - self.open_position['entry_price']) * 100000  # Approximate for XAUUSD
                        else:
                            pnl = (self.open_position['entry_price'] - exit_price) * 100000

                        self.current_balance += pnl
                        trade = {
                            'type': self.open_position['type'],
                            'entry_time': self.open_position['entry_time'],
                            'exit_time': current['time'],
                            'entry_price': self.open_position['entry_price'],
                            'exit_price': exit_price,
                            'exit_type': exit_type,
                            'pnl': pnl,
                            'balance': self.current_balance
                        }
                        self.trades.append(trade)
                        logger.info(f"{exit_type} @ {current['time']}: {exit_price:.5f} | PnL: ${pnl:.2f} | Balance: ${self.current_balance:.2f}")
                        self.open_position = None

            # Print summary
            self.print_summary()
        except Exception as e:
            logger.error(f"Error during backtest: {e}")
        finally:
            self.disconnect_mt5()

    def print_summary(self):
        """Print backtest summary."""
        if not self.trades:
            logger.warning("No trades executed during backtest")
            return

        df_trades = pd.DataFrame(self.trades)
        winning_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] <= 0]

        total_return = self.current_balance - self.initial_balance
        return_percent = (total_return / self.initial_balance) * 100
        win_rate = (len(winning_trades) / len(df_trades)) * 100 if len(df_trades) > 0 else 0

        logger.info("\n" + "="*60)
        logger.info("BACKTEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Initial Balance: ${self.initial_balance:.2f}")
        logger.info(f"Final Balance: ${self.current_balance:.2f}")
        logger.info(f"Total Return: ${total_return:.2f} ({return_percent:.2f}%)")
        logger.info(f"Total Trades: {len(df_trades)}")
        logger.info(f"Winning Trades: {len(winning_trades)}")
        logger.info(f"Losing Trades: {len(losing_trades)}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        if len(winning_trades) > 0:
            logger.info(f"Avg Win: ${winning_trades['pnl'].mean():.2f}")
        if len(losing_trades) > 0:
            logger.info(f"Avg Loss: ${losing_trades['pnl'].mean():.2f}")
        logger.info(f"Max Drawdown: ${df_trades['pnl'].min():.2f}")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    backtester = Backtester(BACKTEST_START_DATE, BACKTEST_END_DATE, BACKTEST_INITIAL_BALANCE)
    backtester.backtest()
