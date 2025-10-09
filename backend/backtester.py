"""
Backtester
Simulerar trading strategi historiskt med 1/3 exit logik
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from stock_data import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from signal_modes import get_mode_config
from confidence_calculator import calculate_confidence
from macro_data import MacroDataFetcher


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
        self.analyzer = TechnicalAnalyzer()
        self.mode_config = get_mode_config(mode)
        self.macro_data = MacroDataFetcher()

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

        # Fetch historical data (includes buffer for indicators)
        all_data = self._fetch_historical_data()
        if all_data is None or all_data.empty:
            return self._generate_results()

        # Filter to backtest period for simulation
        # Convert start_date to timezone-aware if data index is timezone-aware
        if all_data.index.tz is not None:
            start_date_aware = pd.Timestamp(self.start_date).tz_localize(all_data.index.tz)
        else:
            start_date_aware = self.start_date

        backtest_data = all_data[all_data.index >= start_date_aware]

        if backtest_data.empty:
            print(f"No data in backtest period")
            return self._generate_results()

        # Simulate trading day by day (but pass full data for indicator calculation)
        for idx, row in backtest_data.iterrows():
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

            # Generate new signal if no position (pass full data for indicators)
            if not self.position:
                self._check_entry(current_date, current_price, row, all_data)

        # Close any remaining position at end
        if self.position:
            self._close_position(self.end_date, backtest_data.iloc[-1]['Close'], 'END_OF_BACKTEST')

        return self._generate_results()

    def _fetch_historical_data(self):
        """Fetch historical price data using yfinance directly"""
        try:
            import yfinance as yf

            # Add buffer to get enough data for technical indicators
            buffer_start = self.start_date - timedelta(days=200)

            # Get ticker symbol with correct suffix
            symbol = self.stock_data.get_ticker_symbol(self.ticker, self.market)

            # Fetch data directly from yfinance with start/end dates
            stock = yf.Ticker(symbol)
            data = stock.history(
                start=buffer_start.strftime('%Y-%m-%d'),
                end=self.end_date.strftime('%Y-%m-%d'),
                interval='1d'
            )

            if data is None or data.empty:
                print(f"No historical data found for {self.ticker}")
                return None

            # Filter to actual backtest period (keep buffer for indicators)
            # Don't filter yet - we need the buffer data for indicators
            return data

        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def _check_entry(self, date, price, row, historical_data):
        """Check if we should enter a new position using historical data"""
        try:
            # Get data slice up to this date (for indicator calculation)
            data_slice = historical_data.loc[:date].copy()

            if len(data_slice) < 50:  # Need minimum data for indicators
                if len(self.equity_curve) == 1:  # Debug first day only
                    print(f"Skipping {date}: Not enough data ({len(data_slice)} days)")
                return

            # Calculate technical indicators
            rsi = self.analyzer.calculate_rsi(data_slice, period=14)
            macd, macd_signal, macd_hist = self.analyzer.calculate_macd(data_slice)
            adx, plus_di, minus_di = self.analyzer.calculate_adx(data_slice)

            # Get latest values
            current_rsi = rsi.iloc[-1]
            current_macd = macd.iloc[-1]
            current_macd_signal = macd_signal.iloc[-1]
            prev_macd = macd.iloc[-2] if len(macd) > 1 else None
            prev_macd_signal = macd_signal.iloc[-2] if len(macd_signal) > 1 else None
            current_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else None

            # Calculate 20-day MA
            ma20 = data_slice['Close'].rolling(window=20).mean().iloc[-1]

            # Calculate volume ratio
            volume_avg_20 = data_slice['Volume'].tail(20).mean()
            volume_ratio = row['Volume'] / volume_avg_20 if volume_avg_20 > 0 else 1.0

            # Debug: Print indicator values for first few days (optional - comment out for production)
            # if len(self.equity_curve) < 5:
            #     print(f"\n[{date.strftime('%Y-%m-%d')}] Indicator Values:")
            #     print(f"  Price: {price:.2f}, RSI: {current_rsi:.2f}, MACD: {current_macd:.4f}, MA20: {ma20:.2f}")

            # Generate simple buy signal based on technical rules
            score = 0
            reasons = []

            # RSI oversold (more lenient)
            if current_rsi < 45:
                score += 2
                reasons.append(f'RSI oversold ({current_rsi:.1f})')
            elif current_rsi < 50:
                score += 1
                reasons.append(f'RSI neutral ({current_rsi:.1f})')

            # MACD bullish crossover
            if prev_macd is not None and prev_macd_signal is not None:
                if prev_macd < prev_macd_signal and current_macd > current_macd_signal:
                    score += 3
                    reasons.append('MACD bullish crossover')
                elif current_macd > current_macd_signal:
                    score += 1
                    reasons.append('MACD above signal')

            # Price above 20-day MA
            if price > ma20:
                score += 1
                reasons.append('Price above MA20')

            # MACD positive
            if current_macd > 0:
                score += 1
                reasons.append('MACD positive')

            # Positive momentum (price rising)
            if len(data_slice) >= 5:
                price_5d_ago = data_slice['Close'].iloc[-5]
                if price > price_5d_ago:
                    score += 1
                    reasons.append('Positive 5-day momentum')

            # Debug: Print signal scoring (optional - comment out for production)
            # if len(self.equity_curve) < 10:
            #     print(f"  Final Score: {score}, Reasons: {reasons if reasons else 'None'}")

            # Check if signal meets threshold (lowered for backtesting to show trades)
            if score < 1:  # Minimum score to enter (very permissive for demo)
                return

            # PHASE 2 FILTERS: Volume and ADX (prevent low-quality entries)
            # Must have minimum volume (avoid thin trading)
            if volume_ratio < 0.8:  # Below 80% of average = too thin
                return

            # Must have some trend (avoid choppy markets)
            if current_adx is not None and current_adx < 15:  # Too choppy
                return

            # CONFIDENCE CALCULATION (MarketMate Risk-Adjusted)
            # Convert technical score to base_score (-10 to +10 range)
            # Our score ranges from 0 to ~10, so normalize it
            base_score = (score - 5) * 2  # Convert to -10 to +10 range (approximate)

            # Fetch current macro conditions
            try:
                macro_context = self.macro_data.get_all_macro_data()
                vix_data = macro_context.get('vix')
                spx_trend = macro_context.get('spx_trend')
                vix_value = vix_data.get('value') if vix_data else None

                # Calculate confidence
                confidence_result = calculate_confidence(
                    base_score=base_score,
                    vix_value=vix_value,
                    spx_trend=spx_trend,
                    macro_regime=macro_context.get('regime'),
                    macro_score=macro_context.get('macro_score'),
                    sentiment_data=macro_context.get('sentiment')
                )

                recommended_size = confidence_result['recommended_size']
                confidence_pct = confidence_result['confidence']
                risk_factors = confidence_result['risk_factors']

                # Skip trade if confidence is too low (AVOID level)
                if recommended_size == 'none':
                    print(f"[{date.strftime('%Y-%m-%d')}] SKIPPED: Confidence too low ({confidence_pct:.1f}%), Risk: {', '.join(risk_factors)}")
                    return

            except Exception as e:
                # If macro data fails, default to full size (fallback)
                print(f"Warning: Could not calculate confidence, using full position: {e}")
                recommended_size = 'full'
                confidence_pct = 70.0
                risk_factors = []

            # Calculate position size with confidence adjustment
            entry_price = price * (1 + self.slippage)  # Add slippage
            # Reduce capital by commission percentage to ensure total cost doesn't exceed capital
            buyable_capital = self.capital / (1 + self.commission)

            # CONFIDENCE-BASED POSITION SIZING
            if recommended_size == 'quarter':
                buyable_capital *= 0.25  # 25% position
            elif recommended_size == 'half':
                buyable_capital *= 0.5   # 50% position
            # else: full position (100%)

            shares = int(buyable_capital / entry_price)

            if shares == 0:
                return  # Not enough capital

            cost = shares * entry_price * (1 + self.commission)  # Add commission

            if cost > self.capital:
                return  # Not enough capital after commission

            # Calculate stop loss and targets based on mode config
            stop_pct = self.mode_config['stop_loss_buffer'] * 100  # Convert to percentage
            target_mult = self.mode_config['target_multiplier']

            # Base targets
            base_target_1 = 0.04  # 4%
            base_target_2 = 0.08  # 8%
            base_target_3 = 0.15  # 15%

            # Apply mode multiplier to target distances (NOT the price level!)
            target_1_pct = base_target_1 * target_mult
            target_2_pct = base_target_2 * target_mult
            target_3_pct = base_target_3 * target_mult

            # Open position
            self.position = {
                'entry_date': date,
                'entry_price': entry_price,
                'shares': shares,
                'initial_shares': shares,
                'stop_loss': entry_price * (1 - stop_pct / 100),
                'target_1': entry_price * (1 + target_1_pct),
                'target_2': entry_price * (1 + target_2_pct),
                'target_3': entry_price * (1 + target_3_pct),
                'signal': 'BUY',
                'score': score,
                'confidence': confidence_pct,
                'position_size': recommended_size,
                'risk_factors': risk_factors
            }

            self.capital -= cost

            # Build risk warning message
            risk_msg = f" [⚠️ {', '.join(risk_factors[:2])}]" if risk_factors else ""
            size_msg = f" [{recommended_size.upper()}]" if recommended_size != 'full' else ""

            print(f"[{date.strftime('%Y-%m-%d')}] ENTRY: {shares} shares @ {entry_price:.2f} SEK (Score: {score}, Confidence: {confidence_pct:.1f}%{size_msg}{risk_msg})")

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
            'score': self.position['score'],
            'confidence': self.position.get('confidence', 0),
            'position_size': self.position.get('position_size', 'full'),
            'risk_factors': self.position.get('risk_factors', [])
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
