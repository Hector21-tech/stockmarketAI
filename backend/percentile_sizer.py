"""
Percentile-Based Position Sizer
Calculates position sizes based on relative ranking (percentiles) instead of absolute thresholds
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import json
import os


class PercentileSizer:
    """
    Maps stock scores to position sizes using percentile ranking
    Uses 30-day rolling window for adaptive thresholds
    """

    def __init__(self, window_days: int = 30, smooth_days: int = 5):
        """
        Args:
            window_days: Rolling window for percentile calculation (default 30)
            smooth_days: Smoothing window to prevent whipsaws (default 5)
        """
        self.window_days = window_days
        self.smooth_days = smooth_days
        self.history_file = 'percentile_history.json'
        self.score_history = self._load_history()

    def _load_history(self) -> Dict:
        """Load historical scores from disk"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load percentile history: {e}")
                return {}
        return {}

    def _save_history(self):
        """Save historical scores to disk"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.score_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save percentile history: {e}")

    def add_daily_scores(self, date: datetime, scores: List[Dict]):
        """
        Add a day's worth of scores to history

        Args:
            date: Date of the scores
            scores: List of {ticker, score, confidence, ...} dicts from market_scanner
        """
        date_str = date.strftime('%Y-%m-%d')

        # Extract just the scores for percentile calculation
        score_values = [s['score'] for s in scores if s.get('score') is not None]

        if not score_values:
            return

        self.score_history[date_str] = {
            'scores': score_values,
            'mean': float(np.mean(score_values)),
            'median': float(np.median(score_values)),
            'std': float(np.std(score_values)),
            'count': len(score_values)
        }

        # Trim history to window_days + buffer
        self._trim_history(keep_days=self.window_days + 60)  # Keep 60 extra days for safety

        # Save to disk
        self._save_history()

    def _trim_history(self, keep_days: int):
        """Keep only recent N days of history"""
        if not self.score_history:
            return

        dates = sorted(self.score_history.keys())
        cutoff_date = (datetime.now() - timedelta(days=keep_days)).strftime('%Y-%m-%d')

        for date_str in dates:
            if date_str < cutoff_date:
                del self.score_history[date_str]

    def get_percentile(self, score: float, date: datetime = None) -> float:
        """
        Calculate percentile for a given score using rolling window

        Args:
            score: Stock's technical score
            date: Date to calculate percentile for (default: today)

        Returns:
            Percentile (0-100)
        """
        if date is None:
            date = datetime.now()

        # Get window of historical scores
        window_scores = self._get_window_scores(date)

        if len(window_scores) < 10:  # Need minimum data
            # Fallback to absolute scoring if not enough history
            # Assume score range is 0-10, map to percentile
            return min(100, max(0, (score / 10) * 100))

        # Calculate percentile
        percentile = (np.sum(window_scores < score) / len(window_scores)) * 100

        return percentile

    def _get_window_scores(self, end_date: datetime) -> np.ndarray:
        """
        Get all scores within rolling window

        Args:
            end_date: End date of window

        Returns:
            Array of all scores in window
        """
        start_date = end_date - timedelta(days=self.window_days)

        all_scores = []
        for date_str, data in self.score_history.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_date <= date <= end_date:
                all_scores.extend(data['scores'])

        return np.array(all_scores)

    def calculate_position_size(self, score: float, date: datetime = None,
                                 min_size: str = None) -> str:
        """
        Calculate position size based on percentile ranking

        Args:
            score: Stock's technical score
            date: Date for percentile calculation
            min_size: Minimum size override (e.g., 'half' for Top-N)

        Returns:
            Position size: 'full', 'half', 'quarter', or 'none'
        """
        percentile = self.get_percentile(score, date)

        # Map percentile to position size
        if percentile >= 80:  # Top 20%
            size = 'full'
        elif percentile >= 60:  # Top 40%
            size = 'half'
        elif percentile >= 40:  # Top 60%
            size = 'quarter'
        else:  # Bottom 40%
            size = 'none'

        # Apply minimum size override (for Top-N logic)
        if min_size:
            size_rank = {'none': 0, 'quarter': 1, 'half': 2, 'full': 3}
            if size_rank.get(min_size, 0) > size_rank.get(size, 0):
                size = min_size

        return size

    def get_window_stats(self, date: datetime = None) -> Dict:
        """
        Get statistics about the current rolling window

        Args:
            date: Date to calculate stats for (default: today)

        Returns:
            Dict with mean, median, std, percentile thresholds
        """
        if date is None:
            date = datetime.now()

        window_scores = self._get_window_scores(date)

        if len(window_scores) == 0:
            return {'error': 'No historical data in window'}

        return {
            'window_days': self.window_days,
            'data_points': len(window_scores),
            'mean': float(np.mean(window_scores)),
            'median': float(np.median(window_scores)),
            'std': float(np.std(window_scores)),
            'min': float(np.min(window_scores)),
            'max': float(np.max(window_scores)),
            'percentile_80': float(np.percentile(window_scores, 80)),  # Full threshold
            'percentile_60': float(np.percentile(window_scores, 60)),  # Half threshold
            'percentile_40': float(np.percentile(window_scores, 40)),  # Quarter threshold
        }


# Singleton instance
percentile_sizer = PercentileSizer()


# Test
if __name__ == "__main__":
    print("Testing Percentile Sizer...")
    print("=" * 70)

    sizer = PercentileSizer(window_days=30, smooth_days=5)

    # Simulate 30 days of data
    print("\nSimulating 30 days of OMX30 scores...")
    for day in range(30):
        date = datetime.now() - timedelta(days=30-day)

        # Simulate scores for 30 stocks (OMX30)
        # In bull market: higher average scores
        # In bear market: lower average scores
        if day < 15:  # Bull market simulation
            base_score = 6.0
        else:  # Bear market simulation
            base_score = 3.5

        simulated_scores = []
        for i in range(30):
            # Random variation around base score
            score = base_score + np.random.normal(0, 1.5)
            score = max(0, min(10, score))  # Clamp to 0-10
            simulated_scores.append({
                'ticker': f'STOCK{i+1}',
                'score': score
            })

        sizer.add_daily_scores(date, simulated_scores)

    print(f"Added {len(sizer.score_history)} days of historical data")

    # Test percentile calculation
    print("\n" + "=" * 70)
    print("Testing Position Sizing with Different Scores:")
    print("=" * 70)

    test_scores = [2.0, 4.0, 5.5, 7.0, 8.5]
    today = datetime.now()

    print(f"\n{'Score':<10} {'Percentile':<12} {'Size':<12} {'Explanation'}")
    print("-" * 70)

    for score in test_scores:
        percentile = sizer.get_percentile(score, today)
        size = sizer.calculate_position_size(score, today)

        explanation = ""
        if percentile >= 80:
            explanation = "Top 20% - Strong setup"
        elif percentile >= 60:
            explanation = "Top 40% - Good setup"
        elif percentile >= 40:
            explanation = "Top 60% - Moderate setup"
        else:
            explanation = "Bottom 40% - Weak setup"

        print(f"{score:<10.1f} {percentile:<12.1f} {size.upper():<12} {explanation}")

    # Window stats
    print("\n" + "=" * 70)
    print("Rolling Window Statistics:")
    print("=" * 70)

    stats = sizer.get_window_stats(today)
    if 'error' not in stats:
        print(f"  Window: {stats['window_days']} days")
        print(f"  Data points: {stats['data_points']}")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Median: {stats['median']:.2f}")
        print(f"  Std Dev: {stats['std']:.2f}")
        print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
        print(f"\n  Percentile Thresholds:")
        print(f"    80th (Full):    {stats['percentile_80']:.2f}")
        print(f"    60th (Half):    {stats['percentile_60']:.2f}")
        print(f"    40th (Quarter): {stats['percentile_40']:.2f}")

    print("=" * 70)
