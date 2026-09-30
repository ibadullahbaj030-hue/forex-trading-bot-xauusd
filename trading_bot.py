#!/usr/bin/env python3
"""
Main trading bot script for XAUUSD with EMA 20/50 crossover strategy.
Connects to MetaTrader 5 and executes trades based on moving average signals.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from config import (
    MT5_PATH, ACCOUNT_NUMBER, ACCOUNT_PASSWORD, SERVER,
    SYMBOL, TIMEFRAME, FAST_EMA_PERIOD, SLOW_EMA_PERIOD,
    RISK_PERCENT, MAX_STOP_LOSS_PIPS, TAKE_PROFIT_RATIO,
    MAX_OPEN_POSITIONS, TRADING_START_HOUR, TRADING_END_HOUR,
    LOG_FILE, LOG_LEVEL, DEMO_MODE, BACKTEST_MODE,
    EMERGENCY_STOP, MAX_DAILY_LOSS_PERCENT
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


class TradingBot:
    """Main trading bot class for XAUUSD EMA crossover strategy."""

    def __init__(self):
        """Initialize the trading bot."""
        self.connected = False
        self.symbol = SYMBOL
        self.timeframe = TIMEFRAME
        self.fast_period = FAST_EMA_PERIOD
        self.slow_period = SLOW_EMA_PERIOD
        self.risk_percent = RISK_PERCENT
        self.max_sl_pips = MAX_STOP_LOSS_PIPS
        self.tp_ratio = TAKE_PROFIT_RATIO
        self.open_positions = []
        self.trade_count = 0
        self.daily_loss = 0.0
        self.session_start_balance = 0.0
        self.last_signal = None  # Track last signal to avoid duplicate trades
        logger.info("Trading bot initialized")

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

            # Login to account
            if ACCOUNT_NUMBER and ACCOUNT_PASSWORD:
                if not mt5.login(ACCOUNT_NUMBER, ACCOUNT_PASSWORD, SERVER):
                    logger.error(f"Failed to login. Account: {ACCOUNT_NUMBER}, Server: {SERVER}")
                    return False
                logger.info(f"Connected to MT5 - Account: {ACCOUNT_NUMBER}, Server: {SERVER}")
            else:
                logger.warning("Account number or password not set. Using pre-logged-in account.")

            self.connected = True
            self.session_start_balance = self.get_account_balance()
            logger.info(f"Session started with balance: ${self.session_start_balance:.2f}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False

    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5."""
        try:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")

    def get_account_balance(self):
        """Get current account balance."""
        try:
            account_info = mt5.account_info()
            if account_info:
                return account_info.balance
            return 0.0
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return 0.0

    def get_account_equity(self):
        """Get current account equity."""
        try:
            account_info = mt5.account_info()
            if account_info:
                return account_info.equity
            return 0.0
        except Exception as e:
            logger.error(f"Error getting account equity: {e}")
            return 0.0

    def get_rates(self, count=100):
        """Fetch historical rates for the symbol."""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates retrieved for {self.symbol}")
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            return None

    def calculate_ema(self, df, period, column='close'):
        """Calculate Exponential Moving Average."""
        try:
            return df[column].ewm(span=period, adjust=False).mean()
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return None

    def get_signal(self):
        """Generate trading signal based on EMA crossover.
        Returns: 'BUY', 'SELL', or None
        """
        try:
            df = self.get_rates(count=max(self.slow_period + 10, 100))
            if df is None or len(df) < self.slow_period:
                return None

            # Calculate EMAs
            df['ema_fast'] = self.calculate_ema(df, self.fast_period)
            df['ema_slow'] = self.calculate_ema(df, self.slow_period)

            if df['ema_fast'].isna().any() or df['ema_slow'].isna().any():
                return None

            # Get last two candles for crossover detection
            current = df.iloc[-1]
            previous = df.iloc[-2]

            # BUY Signal: Fast EMA crosses above Slow EMA
            if previous['ema_fast'] <= previous['ema_slow'] and \
               current['ema_fast'] > current['ema_slow']:
                return 'BUY'

            # SELL Signal: Fast EMA crosses below Slow EMA
            elif previous['ema_fast'] >= previous['ema_slow'] and \
                 current['ema_fast'] < current['ema_slow']:
                return 'SELL'

            return None
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None

    def get_symbol_info(self):
        """Get symbol information."""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info:
                return symbol_info
            logger.error(f"Symbol info not found: {self.symbol}")
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def calculate_position_size(self, stop_loss_pips):
        """Calculate position size based on risk management."""
        try:
            balance = self.get_account_balance()
            if balance <= 0:
                logger.error("Invalid account balance")
                return 0

            # Calculate risk amount
            risk_amount = balance * (self.risk_percent / 100)

            # Get symbol info
            symbol_info = self.get_symbol_info()
            if not symbol_info:
                return 0

            # Get tick size and tick value
            tick_size = symbol_info.point
            tick_value = symbol_info.trade_tick_value

            if tick_size <= 0 or tick_value <= 0:
                logger.error("Invalid tick size or tick value")
                return 0

            # Calculate lot size
            # Lot size = (Risk Amount) / (Stop Loss in pips * Pip Value)
            pip_value = tick_value / tick_size if tick_size > 0 else 1
            lot_size = risk_amount / (stop_loss_pips * pip_value)

            # Round to minimum lot size
            min_lot = symbol_info.volume_min
            lot_size = max(lot_size, min_lot)

            # Apply maximum lot size
            max_lot = symbol_info.volume_max
            lot_size = min(lot_size, max_lot)

            logger.info(f"Calculated lot size: {lot_size:.2f} (Risk: {risk_amount:.2f}, SL: {stop_loss_pips} pips)")
            return lot_size
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def calculate_stop_loss_and_tp(self, signal, current_price):
        """Calculate stop loss and take profit levels."""
        try:
            symbol_info = self.get_symbol_info()
            if not symbol_info:
                return None, None

            point = symbol_info.point

            if signal == 'BUY':
                # For BUY: SL below entry, TP above entry
                sl_price = current_price - (self.max_sl_pips * point)
                tp_price = current_price + (self.max_sl_pips * self.tp_ratio * point)
            elif signal == 'SELL':
                # For SELL: SL above entry, TP below entry
                sl_price = current_price + (self.max_sl_pips * point)
                tp_price = current_price - (self.max_sl_pips * self.tp_ratio * point)
            else:
                return None, None

            logger.info(f"Stop Loss: {sl_price:.5f}, Take Profit: {tp_price:.5f}")
            return sl_price, tp_price
        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            return None, None

    def place_order(self, signal, volume, sl, tp):
        """Place a trade order."""
        try:
            symbol_info = self.get_symbol_info()
            if not symbol_info:
                logger.error("Failed to get symbol info for order")
                return False

            # Get current price
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                logger.error("Failed to get current price")
                return False

            # Determine order type and price
            if signal == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif signal == 'SELL':
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                logger.error(f"Invalid signal: {signal}")
                return False

            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 12345,
                "comment": f"EMA {self.fast_period}/{self.slow_period} {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed. Retcode: {result.retcode}")
                return False

            logger.info(f"Order placed: {signal} {volume} {self.symbol} @ {price:.5f} (SL: {sl:.5f}, TP: {tp:.5f})")
            self.trade_count += 1
            return True
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def get_open_positions(self):
        """Get all open positions for the symbol."""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions:
                return len(positions)
            return 0
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return 0

    def check_emergency_stop(self):
        """Check if emergency stop conditions are met."""
        if EMERGENCY_STOP:
            logger.critical("EMERGENCY STOP activated!")
            return True

        # Check daily loss limit
        current_balance = self.get_account_balance()
        daily_loss_percent = ((self.session_start_balance - current_balance) / self.session_start_balance) * 100

        if daily_loss_percent > MAX_DAILY_LOSS_PERCENT:
            logger.critical(f"Daily loss limit exceeded: {daily_loss_percent:.2f}% > {MAX_DAILY_LOSS_PERCENT}%")
            return True

        return False

    def is_trading_allowed(self):
        """Check if current time is within trading hours."""
        if TRADING_END_HOUR is None:
            return True  # Trade 24/7

        current_hour = datetime.utcnow().hour
        return TRADING_START_HOUR <= current_hour < TRADING_END_HOUR

    def run(self):
        """Main trading loop."""
        if not self.connect_mt5():
            logger.error("Failed to connect to MT5")
            return

        logger.info(f"Starting trading bot - Symbol: {self.symbol}, Timeframe: {self.timeframe}M")
        logger.info(f"Strategy: EMA {self.fast_period}/{self.slow_period} crossover")
        logger.info(f"Risk per trade: {self.risk_percent}%, Max SL: {self.max_sl_pips} pips")
        logger.info(f"Demo Mode: {DEMO_MODE}")

        try:
            while True:
                if self.check_emergency_stop():
                    logger.critical("Stopping bot due to emergency stop")
                    break

                if not self.is_trading_allowed():
                    logger.debug("Outside trading hours")
                    time.sleep(60)
                    continue

                # Get signal
                signal = self.get_signal()

                if signal and signal != self.last_signal:
                    logger.info(f"Signal generated: {signal}")

                    # Check open positions
                    open_positions = self.get_open_positions()
                    if open_positions >= MAX_OPEN_POSITIONS:
                        logger.warning(f"Max open positions reached: {open_positions}")
                        time.sleep(60)
                        continue

                    # Calculate SL and TP
                    tick = mt5.symbol_info_tick(self.symbol)
                    if not tick:
                        logger.error("Failed to get tick data")
                        time.sleep(60)
                        continue

                    current_price = tick.ask if signal == 'BUY' else tick.bid
                    sl, tp = self.calculate_stop_loss_and_tp(signal, current_price)

                    if sl is None or tp is None:
                        logger.error("Failed to calculate SL/TP")
                        time.sleep(60)
                        continue

                    # Calculate position size
                    sl_pips = abs((current_price - sl) / mt5.symbol_info(self.symbol).point)
                    volume = self.calculate_position_size(sl_pips)

                    if volume <= 0:
                        logger.error("Invalid volume calculated")
                        time.sleep(60)
                        continue

                    # Place order
                    if not DEMO_MODE:
                        if self.place_order(signal, volume, sl, tp):
                            self.last_signal = signal
                    else:
                        logger.info(f"[DEMO] Would place order: {signal} {volume:.2f} {self.symbol}")
                        self.last_signal = signal

                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.critical(f"Unexpected error in main loop: {e}")
        finally:
            self.disconnect_mt5()
            logger.info(f"Trading session ended. Total trades: {self.trade_count}")
            logger.info(f"Final balance: ${self.get_account_balance():.2f}")


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
