"""
Trailing Stop Manager
Handles Chandelier Exit and other trailing stop strategies
"""

import pandas as pd
from typing import Dict, Optional


class TrailingStopManager:
    """
    Manages trailing stops for positions

    Implements Chandelier Exit:
    - Stop = Highest High - (ATR * multiplier)
    - Only raises stop, never lowers
    """

    def __init__(self, atr_multiplier: float = 3.0, atr_period: int = 22):
        """
        Initialize trailing stop manager

        Args:
            atr_multiplier: ATR multiplier for Chandelier Exit (default 3.0)
            atr_period: ATR calculation period (default 22)
        """
        self.atr_multiplier = atr_multiplier
        self.atr_period = atr_period

    def calculate_chandelier_stop(
        self,
        highest_high: float,
        current_atr: float,
        current_stop: Optional[float] = None
    ) -> float:
        """
        Calculate Chandelier Exit stop level

        Formula: Stop = Highest High - (ATR × multiplier)

        Args:
            highest_high: Highest price since entry
            current_atr: Current ATR value
            current_stop: Current stop level (if any)

        Returns:
            New stop level (only raised, never lowered)
        """
        # Calculate new stop level
        new_stop = highest_high - (current_atr * self.atr_multiplier)

        # Only raise stop, never lower it
        if current_stop is not None:
            return max(new_stop, current_stop)

        return new_stop

    def update_stop(
        self,
        position: Dict,
        current_price: float,
        current_atr: float
    ) -> Dict:
        """
        Update position's trailing stop

        Args:
            position: Position dictionary with 'highest_price' and 'stop_loss'
            current_price: Current market price
            current_atr: Current ATR value

        Returns:
            Updated position dictionary
        """
        # Update highest price
        if current_price > position.get('highest_price', current_price):
            position['highest_price'] = current_price

        # Calculate new stop using Chandelier Exit
        highest_high = position['highest_price']
        current_stop = position.get('stop_loss')

        new_stop = self.calculate_chandelier_stop(
            highest_high=highest_high,
            current_atr=current_atr,
            current_stop=current_stop
        )

        # Update position stop
        position['stop_loss'] = new_stop

        return position

    def should_exit(
        self,
        current_price: float,
        stop_loss: float
    ) -> bool:
        """
        Check if trailing stop has been hit

        Args:
            current_price: Current market price
            stop_loss: Current stop loss level

        Returns:
            True if stop hit, False otherwise
        """
        return current_price <= stop_loss

    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 22) -> pd.Series:
        """
        Calculate Average True Range (ATR)

        Args:
            data: DataFrame with High, Low, Close columns
            period: ATR period (default 22 for Chandelier)

        Returns:
            ATR Series
        """
        if len(data) < period + 1:
            return pd.Series([0] * len(data), index=data.index)

        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift()).abs()
        low_close = (data['Low'] - data['Close'].shift()).abs()

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # ATR = rolling mean of True Range
        atr = true_range.rolling(window=period).mean()

        return atr


# Test-funktion
if __name__ == "__main__":
    print("Testing Trailing Stop Manager...")
    print("="*60)

    manager = TrailingStopManager(atr_multiplier=3.0, atr_period=22)

    # Test scenario: Position at 100 SEK, ATR = 2 SEK
    entry_price = 100.0
    atr = 2.0

    # Initial position
    position = {
        'entry_price': entry_price,
        'stop_loss': entry_price - (2 * atr),  # Initial stop at entry - 2×ATR
        'highest_price': entry_price
    }

    print(f"\nInitial Position:")
    print(f"Entry: {position['entry_price']:.2f} SEK")
    print(f"Initial Stop: {position['stop_loss']:.2f} SEK")

    # Simulate price movement
    prices = [102, 105, 108, 110, 112, 115, 113, 111]  # Price goes up then pulls back

    print(f"\nSimulating price movement:")
    print("-"*60)

    for price in prices:
        # Update stop
        position = manager.update_stop(position, price, atr)

        # Check if stopped out
        stopped = manager.should_exit(price, position['stop_loss'])

        print(f"Price: {price:6.2f} | Highest: {position['highest_price']:6.2f} | "
              f"Stop: {position['stop_loss']:6.2f} | "
              f"{'STOPPED OUT' if stopped else 'OK'}")

        if stopped:
            pnl = price - position['entry_price']
            pnl_pct = (pnl / position['entry_price']) * 100
            print(f"\nPosition closed! P/L: {pnl:+.2f} SEK ({pnl_pct:+.1f}%)")
            break

    print("\n" + "="*60)
    print("Test complete!")
