"""
Teknisk Analys Modul
Beraknar RSI, MACD, Stochastic och andra indikatorer enligt Marketmate-strategin
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

class TechnicalAnalyzer:
    """Beraknar tekniska indikatorer"""

    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Beraknar Relative Strength Index (RSI)

        Args:
            data: DataFrame med 'Close' kolumn
            period: RSI-period (default 14)

        Returns:
            Series med RSI-varden
        """
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_macd(data: pd.DataFrame,
                      fast: int = 12,
                      slow: int = 26,
                      signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Beraknar MACD (Moving Average Convergence Divergence)

        Args:
            data: DataFrame med 'Close' kolumn
            fast: Snabb EMA period
            slow: Langsam EMA period
            signal: Signal linje period

        Returns:
            Tuple (MACD line, Signal line, Histogram)
        """
        exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = data['Close'].ewm(span=slow, adjust=False).mean()

        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_stochastic(data: pd.DataFrame,
                            k_period: int = 14,
                            d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Beraknar Stochastic Oscillator

        Args:
            data: DataFrame med 'High', 'Low', 'Close'
            k_period: %K period
            d_period: %D period (smooth)

        Returns:
            Tuple (%K, %D)
        """
        low_min = data['Low'].rolling(window=k_period).min()
        high_max = data['High'].rolling(window=k_period).max()

        k_percent = 100 * ((data['Close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()

        return k_percent, d_percent

    @staticmethod
    def calculate_ema(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Beraknar Exponential Moving Average"""
        return data['Close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_sma(data: pd.DataFrame, period: int = 50) -> pd.Series:
        """Beraknar Simple Moving Average"""
        return data['Close'].rolling(window=period).mean()

    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20,
                                  std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Beraknar Bollinger Bands

        Args:
            data: DataFrame med 'Close' kolumn
            period: Period for SMA (default 20)
            std_dev: Antal standardavvikelser (default 2.0)

        Returns:
            Tuple (upper_band, middle_band, lower_band)
        """
        middle_band = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=period).std()

        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_adx(data: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Beraknar Average Directional Index (ADX) for trend strength

        ADX > 25: Strong trend (tradeable)
        ADX 20-25: Moderate trend
        ADX < 20: Weak/choppy trend (avoid trading)

        Args:
            data: DataFrame med 'High', 'Low', 'Close' kolumner
            period: ADX period (default 14)

        Returns:
            Tuple (adx, plus_di, minus_di)
        """
        # Calculate True Range (TR)
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        # Calculate Directional Movement
        up_move = data['High'] - data['High'].shift()
        down_move = data['Low'].shift() - data['Low']

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        plus_dm_smooth = pd.Series(plus_dm, index=data.index).rolling(window=period).mean()
        minus_dm_smooth = pd.Series(minus_dm, index=data.index).rolling(window=period).mean()

        # Calculate Directional Indicators
        plus_di = 100 * (plus_dm_smooth / atr)
        minus_di = 100 * (minus_dm_smooth / atr)

        # Calculate ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx, plus_di, minus_di

    @staticmethod
    def detect_divergence(price: pd.Series, indicator: pd.Series,
                         window: int = 20) -> str:
        """
        Detekterar bullish/bearish divergens

        Returns:
            'bullish', 'bearish', eller 'none'
        """
        if len(price) < window:
            return 'none'

        price_trend = price.iloc[-window:].diff().mean()
        indicator_trend = indicator.iloc[-window:].diff().mean()

        # Bullish divergence: pris ner, indikator upp
        if price_trend < 0 and indicator_trend > 0:
            return 'bullish'

        # Bearish divergence: pris upp, indikator ner
        if price_trend > 0 and indicator_trend < 0:
            return 'bearish'

        return 'none'

    @staticmethod
    def identify_support_resistance(data: pd.DataFrame,
                                    window: int = 20) -> Dict[str, float]:
        """
        Identifierar stod och motstand med swing levels

        MarketMate-stil: Använder senaste swing highs/lows istället för absoluta extremer

        Returns:
            Dict med 'support' och 'resistance'
        """
        if len(data) < window:
            return {'support': None, 'resistance': None}

        recent_data = data.tail(window).copy()
        current_price = data['Close'].iloc[-1]

        # Swing Low: Lokalt minimum (pris lägre än grannarna)
        # Ta senaste 10 dagar och hitta närmaste swing low
        swing_lows = []
        for i in range(2, min(10, len(recent_data) - 2)):
            idx = len(recent_data) - i - 1
            if (recent_data['Low'].iloc[idx] < recent_data['Low'].iloc[idx-1] and
                recent_data['Low'].iloc[idx] < recent_data['Low'].iloc[idx+1]):
                swing_lows.append(float(recent_data['Low'].iloc[idx]))

        # Swing High: Lokalt maximum
        swing_highs = []
        for i in range(2, min(10, len(recent_data) - 2)):
            idx = len(recent_data) - i - 1
            if (recent_data['High'].iloc[idx] > recent_data['High'].iloc[idx-1] and
                recent_data['High'].iloc[idx] > recent_data['High'].iloc[idx+1]):
                swing_highs.append(float(recent_data['High'].iloc[idx]))

        # Använd närmaste swing levels, fallback till absoluta min/max
        if swing_lows:
            support = max(swing_lows)  # Närmaste swing low
        else:
            support = float(recent_data['Low'].min())

        if swing_highs:
            resistance = min([h for h in swing_highs if h > current_price], default=max(swing_highs))
        else:
            resistance = float(recent_data['High'].max())

        return {
            'support': float(support),
            'resistance': float(resistance)
        }

    def get_full_analysis(self, data: pd.DataFrame) -> Dict:
        """
        Gor komplett teknisk analys pa aktie

        Returns:
            Dict med alla indikatorer och signaler
        """
        if data.empty or len(data) < 50:
            return {'error': 'Insufficient data'}

        # Berakna indikatorer
        rsi = self.calculate_rsi(data)
        macd_line, signal_line, histogram = self.calculate_macd(data)
        k_percent, d_percent = self.calculate_stochastic(data)
        ema_20 = self.calculate_ema(data, 20)
        sma_50 = self.calculate_sma(data, 50)
        adx, plus_di, minus_di = self.calculate_adx(data)

        # Senaste varden
        current_price = float(data['Close'].iloc[-1])
        current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        current_macd = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
        current_signal = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
        current_k = float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else None
        current_d = float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else None
        current_adx = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None
        current_plus_di = float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else None
        current_minus_di = float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else None

        # Stod/Motstand
        levels = self.identify_support_resistance(data)

        # Divergens
        rsi_divergence = self.detect_divergence(data['Close'], rsi) if current_rsi else 'none'

        # Trend
        trend = 'bullish' if current_price > float(ema_20.iloc[-1]) else 'bearish'

        # MACD Crossover
        macd_crossover = 'bullish' if current_macd and current_signal and current_macd > current_signal else 'bearish'

        return {
            'price': current_price,
            'rsi': current_rsi,
            'rsi_status': self._get_rsi_status(current_rsi),
            'rsi_divergence': rsi_divergence,
            'macd': {
                'macd_line': current_macd,
                'signal_line': current_signal,
                'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None,
                'crossover': macd_crossover
            },
            'stochastic': {
                'k': current_k,
                'd': current_d,
                'status': self._get_stoch_status(current_k, current_d)
            },
            'adx': {
                'adx': current_adx,
                'plus_di': current_plus_di,
                'minus_di': current_minus_di,
                'trend_strength': self._get_adx_status(current_adx)
            },
            'trend': trend,
            'ema_20': float(ema_20.iloc[-1]),
            'sma_50': float(sma_50.iloc[-1]),
            'support': levels['support'],
            'resistance': levels['resistance'],
            'volume': float(data['Volume'].iloc[-1]),
            'volume_avg_20': float(data['Volume'].tail(20).mean()),  # 20-dagars genomsnitt
            'volume_ratio': float(data['Volume'].iloc[-1] / data['Volume'].tail(20).mean())  # Current / Average
        }

    @staticmethod
    def _get_rsi_status(rsi: Optional[float]) -> str:
        """Tolkar RSI-niva"""
        if rsi is None:
            return 'unknown'
        if rsi > 70:
            return 'overbought'
        elif rsi < 30:
            return 'oversold'
        else:
            return 'neutral'

    @staticmethod
    def _get_stoch_status(k: Optional[float], d: Optional[float]) -> str:
        """Tolkar Stochastic-niva"""
        if k is None or d is None:
            return 'unknown'
        if k > 80 and d > 80:
            return 'overbought'
        elif k < 20 and d < 20:
            return 'oversold'
        else:
            return 'neutral'

    @staticmethod
    def _get_adx_status(adx: Optional[float]) -> str:
        """Tolkar ADX-niva (trend strength)"""
        if adx is None:
            return 'unknown'
        if adx > 25:
            return 'strong'  # Strong trend - tradeable
        elif adx > 20:
            return 'moderate'  # Moderate trend
        else:
            return 'weak'  # Weak/choppy - avoid trading


# Test-funktion
if __name__ == "__main__":
    from stock_data import StockDataFetcher

    print("Testing Technical Analysis...")
    print("="*60)

    fetcher = StockDataFetcher()
    analyzer = TechnicalAnalyzer()

    # Test med VOLVO-B
    ticker = "VOLVO-B"
    print(f"\nAnalyserar {ticker}...")

    data = fetcher.get_historical_data(ticker, period="3mo", market="SE")

    if not data.empty:
        analysis = analyzer.get_full_analysis(data)

        print(f"\nPris: {analysis['price']} SEK")
        print(f"RSI: {analysis['rsi']:.2f} ({analysis['rsi_status']})")
        print(f"RSI Divergens: {analysis['rsi_divergence']}")
        print(f"MACD Crossover: {analysis['macd']['crossover']}")
        print(f"Stochastic: K={analysis['stochastic']['k']:.2f}, D={analysis['stochastic']['d']:.2f} ({analysis['stochastic']['status']})")
        print(f"Trend: {analysis['trend']}")
        print(f"Stod: {analysis['support']:.2f} SEK")
        print(f"Motstand: {analysis['resistance']:.2f} SEK")
