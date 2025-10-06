#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marketsmakers.py — Single-file toolkit for MarketMate / MarketsMakers

All-in-one module you can drop into your app.
Focus:
- Data fetching (pluggable: yfinance, Polygon, Finnhub, Alpha Vantage)
- Indicators: RSI, MACD, Stochastic, Bollinger Bands, EMA/SMA, ATR
- Patterns (basic): golden/death cross, engulfing (stub), head & shoulders (stub)
- Multi-timeframe aggregation
- Risk: position sizing, R/R, Kelly (fractional), drawdown
- Backtesting (vectorized), performance (CAGR, Sharpe, Sortino, MaxDD, WinRate)
- Alerts (rules + hooks), simple strategy registry
- Macro placeholders (FRED: M2, Fed Funds, DXY, VIX)
- Config + simple CLI

Dependencies (install in your environment, not required here):
    pip install pandas numpy yfinance scipy

Author: You + GPT-5 Thinking
License: MIT
"""
from __future__ import annotations

import math
import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Tuple, Any
from datetime import datetime
import numpy as np
import pandas as pd

# ============== CONFIG ==============

@dataclass
class MMConfig:
    data_source: str = "yfinance"  # or "polygon", "alphavantage", "finnhub"
    tz: str = "Europe/Stockholm"
    risk_free_rate_annual: float = 0.02  # 2%
    default_start: str = "2015-01-01"
    default_end: Optional[str] = None  # None = today
    # For yfinance
    yf_interval: str = "1d"  # 1m, 5m, 1h, 1d, 1wk
    # Backtest
    slippage_bps: float = 1.0  # 1 basis point
    commission_bps: float = 2.5
    initial_capital: float = 100_000.0

CONFIG = MMConfig()

# ============== DATA FETCHER (PLUGGABLE) ==============

class DataFetcher:
    """
    Pluggable data fetcher. Default uses yfinance.
    Implement your own fetch_<source>() for other providers.
    """
    def __init__(self, config: MMConfig = CONFIG):
        self.cfg = config

    def fetch(self, ticker: str, start: Optional[str]=None, end: Optional[str]=None,
              interval: Optional[str]=None) -> pd.DataFrame:
        start = start or self.cfg.default_start
        end = end or self.cfg.default_end
        interval = interval or self.cfg.yf_interval

        if self.cfg.data_source == "yfinance":
            return self._fetch_yfinance(ticker, start, end, interval)
        raise ValueError(f"Unsupported data source: {self.cfg.data_source}")

    def _fetch_yfinance(self, ticker: str, start: str, end: Optional[str], interval: str) -> pd.DataFrame:
        try:
            import yfinance as yf  # type: ignore
        except Exception as e:
            raise RuntimeError("yfinance not installed. Run: pip install yfinance") from e

        df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise RuntimeError(f"No data returned for {ticker} {interval}.")
        df = df.rename(columns=str.title)  # Open High Low Close Volume
        # Ensure standard columns
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                raise RuntimeError(f"Missing column {col} in downloaded data.")
        return df

# ============== INDICATORS ==============

class Indicators:
    @staticmethod
    def sma(series: pd.Series, length: int) -> pd.Series:
        return series.rolling(length).mean()

    @staticmethod
    def ema(series: pd.Series, length: int) -> pd.Series:
        return series.ewm(span=length, adjust=False).mean()

    @staticmethod
    def rsi(close: pd.Series, length: int=14) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(length).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(length).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(close: pd.Series, fast: int=12, slow: int=26, signal: int=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = Indicators.ema(close, fast)
        ema_slow = Indicators.ema(close, slow)
        macd = ema_fast - ema_slow
        signal_line = Indicators.ema(macd, signal)
        hist = macd - signal_line
        return macd, signal_line, hist

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k: int=14, d: int=3) -> Tuple[pd.Series, pd.Series]:
        lowest_low = low.rolling(k).min()
        highest_high = high.rolling(k).max()
        k_line = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_line = k_line.rolling(d).mean()
        return k_line, d_line

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int=14) -> pd.Series:
        prev_close = close.shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        return tr.rolling(length).mean()

    @staticmethod
    def bollinger(close: pd.Series, length: int=20, std_mult: float=2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ma = close.rolling(length).mean()
        std = close.rolling(length).std()
        upper = ma + std_mult * std
        lower = ma - std_mult * std
        return ma, upper, lower

# ============== PATTERNS (BASIC) ==============

class Patterns:
    @staticmethod
    def golden_death_cross(close: pd.Series, fast: int=50, slow: int=200) -> pd.Series:
        fast_ma = Indicators.sma(close, fast)
        slow_ma = Indicators.sma(close, slow)
        signal = pd.Series(0, index=close.index)
        signal[(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))] = 1  # golden
        signal[(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))] = -1 # death
        return signal

    @staticmethod
    def engulfing_stub(df: pd.DataFrame) -> pd.Series:
        # Placeholder for candlestick pattern detection
        return pd.Series(0, index=df.index, dtype=int)

    @staticmethod
    def head_shoulders_stub(df: pd.DataFrame) -> pd.Series:
        return pd.Series(0, index=df.index, dtype=int)

# ============== RISK & PERFORMANCE ==============

@dataclass
class Trade:
    dt: pd.Timestamp
    side: str  # 'long' or 'flat' (this simple engine goes flat/long)
    price: float
    size: float  # number of shares
    equity: float

class Risk:
    @staticmethod
    def position_size(capital: float, entry: float, stop: float, risk_pct: float=0.01) -> int:
        risk_per_share = max(entry - stop, 0.01)
        risk_cap = capital * risk_pct
        size = int(risk_cap / risk_per_share)
        return max(size, 0)

    @staticmethod
    def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
        if avg_loss <= 0:
            return 0.0
        b = avg_win / avg_loss
        f = win_rate - (1 - win_rate) / b
        return max(0.0, min(f, 1.0))

class Performance:
    @staticmethod
    def equity_curve(returns: pd.Series, initial: float) -> pd.Series:
        return initial * (1 + returns.fillna(0)).cumprod()

    @staticmethod
    def drawdown(equity: pd.Series) -> pd.Series:
        peak = equity.cummax()
        dd = (equity - peak) / peak
        return dd

    @staticmethod
    def sharpe(returns: pd.Series, rf: float=CONFIG.risk_free_rate_annual, periods_per_year: int=252) -> float:
        excess = returns - (rf / periods_per_year)
        if excess.std(ddof=0) == 0:
            return 0.0
        return np.sqrt(periods_per_year) * excess.mean() / excess.std(ddof=0)

    @staticmethod
    def sortino(returns: pd.Series, rf: float=CONFIG.risk_free_rate_annual, periods_per_year: int=252) -> float:
        excess = returns - (rf / periods_per_year)
        downside = excess[excess < 0]
        denom = downside.std(ddof=0)
        if denom == 0 or np.isnan(denom):
            return 0.0
        return np.sqrt(periods_per_year) * excess.mean() / denom

    @staticmethod
    def cagr(equity: pd.Series, periods_per_year: int=252) -> float:
        if equity.empty:
            return 0.0
        n_periods = len(equity)
        total_return = equity.iloc[-1] / equity.iloc[0]
        years = n_periods / periods_per_year
        return total_return ** (1 / max(years, 1e-9)) - 1

# ============== STRATEGY & BACKTEST ==============

class Strategy:
    """
    Simple rules-based strategy:
      - signal: +1 long, 0 flat
      - position transitions on signal changes
    """
    def __init__(self, name: str, signal_fn: Callable[[pd.DataFrame], pd.Series]):
        self.name = name
        self.signal_fn = signal_fn

    def run(self, df: pd.DataFrame) -> pd.Series:
        return self.signal_fn(df).fillna(0).astype(int)

class Backtester:
    def __init__(self, config: MMConfig = CONFIG):
        self.cfg = config

    def run(self, df: pd.DataFrame, signal: pd.Series) -> Dict[str, Any]:
        # Ensure alignment
        df = df.copy()
        df["Signal"] = signal.reindex(df.index).fillna(0).astype(int)

        # Daily returns
        ret = df["Close"].pct_change().fillna(0)
        pos = df["Signal"].replace(0, np.nan).ffill().fillna(0)  # hold last position
        strat_ret = ret * pos

        # Slippage/commissions on position changes
        changes = df["Signal"].diff().fillna(0).abs()
        costs = changes * (self.cfg.slippage_bps + self.cfg.commission_bps) / 10_000.0
        strat_ret = strat_ret - costs

        equity = Performance.equity_curve(strat_ret, self.cfg.initial_capital)
        dd = Performance.drawdown(equity)

        metrics = {
            "CAGR": Performance.cagr(equity),
            "Sharpe": Performance.sharpe(strat_ret),
            "Sortino": Performance.sortino(strat_ret),
            "MaxDrawdown": dd.min(),
            "WinRate": (strat_ret > 0).mean(),
            "TradesApprox": int(changes.sum() / 2),  # approx entries
            "FinalEquity": float(equity.iloc[-1]),
        }
        return {"equity": equity, "returns": strat_ret, "drawdown": dd, "metrics": metrics}

# ============== MACRO PLACEHOLDERS ==============

class MacroData:
    """
    Stubs for macro integrations. Fill with FRED, Quandl, etc.
    """
    @staticmethod
    def m2_money_supply() -> pd.DataFrame:
        # TODO: integrate FRED ("M2SL") via fredapi
        return pd.DataFrame()

    @staticmethod
    def fed_funds_rate() -> pd.DataFrame:
        # TODO: FRED "FEDFUNDS"
        return pd.DataFrame()

    @staticmethod
    def dxy() -> pd.DataFrame:
        # Fetch via yfinance "DX-Y.NYB" or "DXY"
        return pd.DataFrame()

    @staticmethod
    def vix() -> pd.DataFrame:
        # Fetch via yfinance "^VIX"
        return pd.DataFrame()

# ============== STRATEGY REGISTRY (EXAMPLES) ==============

def strat_rsi_macd(df: pd.DataFrame,
                   rsi_len: int=14, rsi_low: int=30, rsi_high: int=70,
                   fast: int=12, slow: int=26, signal: int=9) -> pd.Series:
    rsi = Indicators.rsi(df["Close"], rsi_len)
    macd, sig, hist = Indicators.macd(df["Close"], fast, slow, signal)
    long = (rsi < rsi_low) & (macd > sig)
    flat = (rsi > rsi_high) & (macd < sig)
    sig_series = pd.Series(0, index=df.index)
    sig_series[long] = +1
    sig_series[flat] = 0
    return sig_series

def strat_golden_cross(df: pd.DataFrame, fast: int=50, slow: int=200) -> pd.Series:
    cross = Patterns.golden_death_cross(df["Close"], fast, slow)
    # Hold long when above, flat when below
    pos = (Indicators.sma(df["Close"], fast) > Indicators.sma(df["Close"], slow)).astype(int)
    # Mark explicit switches on cross for cost accounting; pos drives exposure
    return pos

STRATEGIES: Dict[str, Strategy] = {
    "rsi_macd": Strategy("rsi_macd", strat_rsi_macd),
    "golden_cross": Strategy("golden_cross", strat_golden_cross),
}

# ============== MULTI-TIMEFRAME AGGREGATION ==============

def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """
    Resample OHLCV to a higher timeframe (e.g., 'W', 'M', '4H' not standard in pandas; use '4H' if intraday).
    """
    o = df["Open"].resample(rule).first()
    h = df["High"].resample(rule).max()
    l = df["Low"].resample(rule).min()
    c = df["Close"].resample(rule).last()
    v = df["Volume"].resample(rule).sum()
    out = pd.concat([o, h, l, c, v], axis=1)
    out.columns = ["Open", "High", "Low", "Close", "Volume"]
    return out.dropna()

# ============== ALERTS (RULES + HOOKS) ==============

@dataclass
class AlertRule:
    name: str
    condition: Callable[[pd.DataFrame], pd.Series]  # returns boolean Series
    on_trigger: Optional[Callable[[pd.Timestamp, Dict[str, Any]], None]] = None

class AlertsEngine:
    def __init__(self, rules: List[AlertRule]):
        self.rules = rules

    def run(self, df: pd.DataFrame) -> List[Tuple[str, pd.Timestamp]]:
        triggers = []
        for rule in self.rules:
            mask = rule.condition(df)
            for ts in df.index[mask.fillna(False)]:
                triggers.append((rule.name, ts))
                if rule.on_trigger:
                    try:
                        rule.on_trigger(ts, {"row": df.loc[ts].to_dict()})
                    except Exception:
                        pass
        return triggers

# ============== SIMPLE CLI ==============

def _demo_cli():
    import argparse
    p = argparse.ArgumentParser(description="MarketsMakers single-file toolkit")
    p.add_argument("--ticker", default="AAPL", help="Symbol (e.g., AAPL, VOLV-B.ST)")
    p.add_argument("--start", default=CONFIG.default_start)
    p.add_argument("--end", default=CONFIG.default_end)
    p.add_argument("--interval", default=CONFIG.yf_interval)
    p.add_argument("--strategy", default="rsi_macd", choices=list(STRATEGIES.keys()))
    args = p.parse_args()

    fetcher = DataFetcher(CONFIG)
    df = fetcher.fetch(args.ticker, args.start, args.end, args.interval)
    # Ensure DateTimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    strat = STRATEGIES[args.strategy]
    signal = strat.run(df)

    bt = Backtester(CONFIG)
    res = bt.run(df, signal)

    metrics = res["metrics"]
    print("=== MarketsMakers Backtest ===")
    print(f"Ticker      : {args.ticker}")
    print(f"Strategy    : {strat.name}")
    print(f"Final Equity: {metrics['FinalEquity']:.2f}")
    print(f"CAGR        : {metrics['CAGR']:.2%}")
    print(f"Sharpe      : {metrics['Sharpe']:.2f}")
    print(f"Sortino     : {metrics['Sortino']:.2f}")
    print(f"MaxDD       : {metrics['MaxDrawdown']:.2%}")
    print(f"WinRate     : {metrics['WinRate']:.2%}")
    print(f"Trades ~    : {metrics['TradesApprox']}")

if __name__ == "__main__":
    _demo_cli()
