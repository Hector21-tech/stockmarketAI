"""
Backtester
Simulerar trading strategi historiskt med 1/3 exit logik
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from stock_data import StockDataFetcher
from ai_engine import AIEngine
from signal_modes import get_mode_config


class Backtester:
    def __init__(self, ticker, market='SE', start_date=None, end_date=None,
                 initial_capital=100000, mode='conservative',
                 slippage=0.001, commission=0.0025):
        """
        Initialize backtester

        Args:
            ticker: Stock ticker
            market: Market (SE or US)
            start_date: Start date (YYYY-MM-DD) or None for 1 year back
            end_date: End date (YYYY-MM-DD) or None for today
            initial_capital: Starting capital
            mode: Signal mode (conservative/aggressive/ai-hybrid)
            slippage: Price slippage per trade (0.1% default)
            commission: Commission per trade (0.25% default)
        """
        self.ticker = ticker
        self.market = market
        self.initial_capital = initial_capital
        self.mode = mode
        self.slippage = slippage
        self.commission = commission

        # Setup dates
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else (self.end_date - timedelta(days=365))

        # Components
        self.stock_data = StockDataFetcher()
        self.ai_engine = AIEngine()
        self.mode_config = get_mode_config(mode)

        # State
        self.capital = initial_capital
        self.position = None  # Current position
        self.trades = []  # Completed trades
        self.equity_curve = []  # Portfolio value over time

    def run(self):
        """Run backtest"""
        print(f"\nRunning backtest for {self.ticker} ({self.market})")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Mode: {self.mode}, Capital: {self.initial_capital:,.0f} SEK\n")

        # Fetch historical data
        historical_data = self._fetch_historical_data()
        if historical_data is None or historical_data.empty:
            return self._generate_results()

        # Simulate trading day by day
        for idx, row in historical_data.iterrows():
            current_date = idx
            current_price = row['Close']

            # Update equity curve
            portfolio_value = self._calculate_portfolio_value(current_price)
            self.equity_curve.append({
                'date': current_date,
                'value': portfolio_value,
                'capital': self.capital
            })

            # Check open position for exits
            if self.position:
                self._check_exits(current_date, current_price, row)

            # Generate new signal if no position
            if not self.position:
                self._check_entry(current_date, current_price, row, historical_data)

        # Close any remaining position at end
        if self.position:
            self._close_position(self.end_date, historical_data.iloc[-1]['Close'], 'END_OF_BACKTEST')

        return self._generate_results()

    def _fetch_historical_data(self):
        """Fetch historical price data"""
        try:
            # Add buffer to get enough data for technical indicators
            buffer_start = self.start_date - timedelta(days=200)

            data = self.stock_data.get_historical_data(
                self.ticker,
                self.market,
                period=None,
                interval='1d',
                start=buffer_start.strftime('%Y-%m-%d'),
                end=self.end_date.strftime('%Y-%m-%d')
            )

            if data is None or data.empty:
                print(f"No historical data found for {self.ticker}")
                return None

            # Filter to actual backtest period
            data = data[data.index >= self.start_date]

            return data

        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def _check_entry(self, date, price, row, historical_data):
        """Check if we should enter a new position"""
        try:
            # Generate signal using AI engine
            signal = self.ai_engine.generate_signal(
                self.ticker,
                self.market,
                mode=self.mode
            )

            if not signal:
                return

            # Only enter on BUY or STRONG_BUY
            if signal['action'] not in ['BUY', 'STRONG_BUY']:
                return

            # Check minimum score threshold
            min_score = self.mode_config['buy_threshold']
            if signal['score'] < min_score:
                return

            # Calculate position size (use all available capital)
            entry_price = price * (1 + self.slippage)  # Add slippage
            shares = int(self.capital / entry_price)

            if shares == 0:
                return  # Not enough capital

            cost = shares * entry_price * (1 + self.commission)  # Add commission

            if cost > self.capital:
                return  # Not enough capital after commission

            # Open position
            self.position = {
                'entry_date': date,
                'entry_price': entry_price,
                'shares': shares,
                'initial_shares': shares,
                'stop_loss': signal.get('stop_loss', entry_price * 0.975),
                'target_1': signal.get('target_1', entry_price * 1.04),
                'target_2': signal.get('target_2', entry_price * 1.08),
                'target_3': signal.get('target_3', entry_price * 1.15),
                'signal': signal['action'],
                'score': signal['score']
            }

            self.capital -= cost

            print(f"[{date.strftime('%Y-%m-%d')}] ENTRY: {shares} shares @ {entry_price:.2f} SEK (Score: {signal['score']:.1f})")

        except Exception as e:
            print(f"Error checking entry: {e}")

    def _check_exits(self, date, price, row):
        """Check if any exit conditions are met"""
        if not self.position:
            return

        shares_to_sell = 0
        exit_reason = None
        exit_price = price

        # Check stop loss (sells all remaining shares)
        if price <= self.position['stop_loss']:
            shares_to_sell = self.position['shares']
            exit_reason = 'STOP_LOSS'
            exit_price = price * (1 - self.slippage)  # Worse price on stop loss

        # Check Target 3 (sell final 1/3)
        elif price >= self.position['target_3'] and self.position['shares'] > 0:
            shares_to_sell = self.position['shares']  # Sell all remaining
            exit_reason = 'TARGET_3'
            exit_price = price * (1 - self.slippage)

        # Check Target 2 (sell 1/3)
        elif price >= self.position['target_2'] and self.position['shares'] >= (self.position['initial_shares'] * 2 / 3):
            shares_to_sell = int(self.position['initial_shares'] / 3)
            exit_reason = 'TARGET_2'
            exit_price = price * (1 - self.slippage)

        # Check Target 1 (sell 1/3)
        elif price >= self.position['target_1'] and self.position['shares'] == self.position['initial_shares']:
            shares_to_sell = int(self.position['initial_shares'] / 3)
            exit_reason = 'TARGET_1'
            exit_price = price * (1 - self.slippage)

        if shares_to_sell > 0:
            self._execute_exit(date, exit_price, shares_to_sell, exit_reason)

    def _execute_exit(self, date, price, shares, reason):
        """Execute a partial or full exit"""
        proceeds = shares * price * (1 - self.commission)  # Subtract commission
        self.capital += proceeds

        # Calculate P/L for this exit
        cost_basis = shares * self.position['entry_price']
        pnl = proceeds - cost_basis
        pnl_percent = (pnl / cost_basis) * 100

        # Record trade
        trade = {
            'entry_date': self.position['entry_date'],
            'exit_date': date,
            'ticker': self.ticker,
            'shares': shares,
            'entry_price': self.position['entry_price'],
            'exit_price': price,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': reason,
            'signal': self.position['signal'],
            'score': self.position['score']
        }
        self.trades.append(trade)

        # Update position
        self.position['shares'] -= shares

        print(f"[{date.strftime('%Y-%m-%d')}] EXIT ({reason}): {shares} shares @ {price:.2f} SEK, P/L: {pnl:+.2f} SEK ({pnl_percent:+.1f}%)")

        # Close position if all shares sold
        if self.position['shares'] == 0:
            self.position = None

    def _close_position(self, date, price, reason):
        """Force close position at end of backtest"""
        if self.position and self.position['shares'] > 0:
            self._execute_exit(date, price * (1 - self.slippage), self.position['shares'], reason)

    def _calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value (capital + position value)"""
        position_value = 0
        if self.position:
            position_value = self.position['shares'] * current_price
        return self.capital + position_value

    def _generate_results(self):
        """Generate backtest results with metrics"""
        if not self.trades and not self.equity_curve:
            return {
                'error': 'No trades executed during backtest period',
                'metrics': {},
                'trades': [],
                'equity_curve': []
            }

        # Calculate metrics
        final_value = self.capital
        if self.position:
            final_value += self.position['shares'] * self.equity_curve[-1]['value']

        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100

        # Calculate CAGR
        days = (self.end_date - self.start_date).days
        years = days / 365.25
        cagr = (((final_value / self.initial_capital) ** (1 / years)) - 1) * 100 if years > 0 else 0

        # Calculate win rate
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        win_rate = (len(winning_trades) / len(self.trades) * 100) if self.trades else 0

        # Calculate average gain/loss
        avg_gain = np.mean([t['pnl_percent'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_percent'] for t in losing_trades]) if losing_trades else 0

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio()

        metrics = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'cagr': cagr,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_gain': avg_gain,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': abs(avg_gain / avg_loss) if avg_loss != 0 else 0,
            'total_pnl': sum([t['pnl'] for t in self.trades])
        }

        return {
            'metrics': metrics,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'config': {
                'ticker': self.ticker,
                'market': self.market,
                'mode': self.mode,
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d')
            }
        }

    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown from equity curve"""
        if not self.equity_curve:
            return 0

        values = [point['value'] for point in self.equity_curve]
        peak = values[0]
        max_dd = 0

        for value in values:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self):
        """Calculate Sharpe ratio (simplified)"""
        if not self.trades:
            return 0

        returns = [t['pnl_percent'] for t in self.trades]

        if len(returns) < 2:
            return 0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        # Annualized Sharpe (assuming ~252 trading days)
        sharpe = (mean_return / std_return) * np.sqrt(252 / len(self.trades))

        return sharpe
