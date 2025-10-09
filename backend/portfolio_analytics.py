"""
Portfolio Analytics - Beräknar trading metrics och performance
"""

from datetime import datetime
from typing import Dict, List, Optional
from trade_manager import TradeManager, Position
from stock_data import StockDataFetcher


class PortfolioAnalytics:
    """
    Analyserar portfolio performance och trade metrics
    """

    def __init__(self, trade_manager: TradeManager):
        self.trade_manager = trade_manager
        self.fetcher = StockDataFetcher()

    def calculate_total_pnl(self) -> Dict:
        """
        Beräknar total P/L (realized + unrealized)

        Returns:
            Dict med realized_pnl, unrealized_pnl, total_pnl
        """
        realized_pnl = 0.0
        unrealized_pnl = 0.0

        for position in self.trade_manager.positions:
            # Realized P/L från alla exits
            for exit_record in position.exits:
                realized_pnl += exit_record['profit_per_share'] * exit_record['shares']

            # Unrealized P/L från kvarvarande aktier
            if position.current_shares > 0:
                current_price = self.fetcher.get_current_price(position.ticker, position.market)
                if current_price:
                    unrealized_pnl += (current_price - position.entry_price) * position.current_shares

        return {
            'realized_pnl': round(realized_pnl, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'total_pnl': round(realized_pnl + unrealized_pnl, 2)
        }

    def calculate_win_rate(self) -> Dict:
        """
        Beräknar win rate från stängda positioner

        Returns:
            Dict med total_trades, winning_trades, losing_trades, win_rate
        """
        closed_positions = [p for p in self.trade_manager.positions if p.status == "CLOSED"]

        total_trades = len(closed_positions)
        winning_trades = 0
        losing_trades = 0

        for position in closed_positions:
            # Beräkna total P/L för positionen
            total_exit_pnl = sum(exit_rec['profit_per_share'] * exit_rec['shares']
                                for exit_rec in position.exits)

            if total_exit_pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 1)
        }

    def calculate_average_metrics(self) -> Dict:
        """
        Beräknar average gain/loss och best/worst trades

        Returns:
            Dict med avg_gain, avg_loss, best_trade, worst_trade
        """
        closed_positions = [p for p in self.trade_manager.positions if p.status == "CLOSED"]

        gains = []
        losses = []
        all_pnls = []

        for position in closed_positions:
            # Total P/L för positionen
            total_pnl = sum(exit_rec['profit_per_share'] * exit_rec['shares']
                           for exit_rec in position.exits)

            all_pnls.append(total_pnl)

            if total_pnl > 0:
                gains.append(total_pnl)
            else:
                losses.append(total_pnl)

        avg_gain = (sum(gains) / len(gains)) if gains else 0
        avg_loss = (sum(losses) / len(losses)) if losses else 0
        best_trade = max(all_pnls) if all_pnls else 0
        worst_trade = min(all_pnls) if all_pnls else 0

        return {
            'avg_gain': round(avg_gain, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2)
        }

    def get_trade_history(self) -> List[Dict]:
        """
        Hämtar historik över alla stängda positioner

        Returns:
            Lista med trade historik (sorterad efter datum, nyaste först)
        """
        history = []

        for position in self.trade_manager.positions:
            if position.status == "CLOSED":
                # Beräkna total P/L och % för positionen
                total_pnl = sum(exit_rec['profit_per_share'] * exit_rec['shares']
                               for exit_rec in position.exits)

                total_pnl_percent = sum(exit_rec['profit_percent'] * exit_rec['shares']
                                       for exit_rec in position.exits) / position.initial_shares

                # Datum för sista exit
                last_exit_date = position.exits[-1]['date'] if position.exits else position.entry_date

                history.append({
                    'ticker': position.ticker,
                    'entry_date': position.entry_date,
                    'exit_date': last_exit_date,
                    'entry_price': position.entry_price,
                    'shares': position.initial_shares,
                    'total_pnl': round(total_pnl, 2),
                    'total_pnl_percent': round(total_pnl_percent, 2),
                    'exits': position.exits,
                    'market': position.market
                })

        # Sortera efter exit_date, nyaste först
        history.sort(key=lambda x: x['exit_date'], reverse=True)

        return history

    def get_open_positions_summary(self) -> List[Dict]:
        """
        Hämtar summary över öppna positioner med unrealized P/L

        Returns:
            Lista med öppna positioner och deras current P/L
        """
        open_positions = []

        for position in self.trade_manager.positions:
            if position.current_shares > 0:
                current_price = self.fetcher.get_current_price(position.ticker, position.market)

                if current_price:
                    unrealized_pnl = (current_price - position.entry_price) * position.current_shares
                    unrealized_pnl_percent = ((current_price - position.entry_price) / position.entry_price) * 100

                    # Realized P/L från exits
                    realized_pnl = sum(exit_rec['profit_per_share'] * exit_rec['shares']
                                      for exit_rec in position.exits)

                    open_positions.append({
                        'ticker': position.ticker,
                        'entry_price': position.entry_price,
                        'current_price': current_price,
                        'current_shares': position.current_shares,
                        'initial_shares': position.initial_shares,
                        'entry_date': position.entry_date,
                        'unrealized_pnl': round(unrealized_pnl, 2),
                        'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
                        'realized_pnl': round(realized_pnl, 2),
                        'status': position.status,
                        'market': position.market
                    })

        return open_positions

    def get_full_analytics(self) -> Dict:
        """
        Hämtar all analytics data i ett anrop

        Returns:
            Dict med all portfolio analytics
        """
        pnl_data = self.calculate_total_pnl()
        win_rate_data = self.calculate_win_rate()
        avg_metrics = self.calculate_average_metrics()

        return {
            'pnl': pnl_data,
            'win_rate': win_rate_data,
            'metrics': avg_metrics,
            'open_positions': self.get_open_positions_summary(),
            'closed_trades_count': win_rate_data['total_trades'],
            'timestamp': datetime.now().isoformat()
        }


# Test-funktion
if __name__ == "__main__":
    tm = TradeManager()
    analytics = PortfolioAnalytics(tm)

    print("Portfolio Analytics Test")
    print("=" * 60)

    full_data = analytics.get_full_analytics()

    print("\nP/L Summary:")
    print(f"  Realized: {full_data['pnl']['realized_pnl']} kr")
    print(f"  Unrealized: {full_data['pnl']['unrealized_pnl']} kr")
    print(f"  Total: {full_data['pnl']['total_pnl']} kr")

    print("\nWin Rate:")
    print(f"  Total Trades: {full_data['win_rate']['total_trades']}")
    print(f"  Winning: {full_data['win_rate']['winning_trades']}")
    print(f"  Win Rate: {full_data['win_rate']['win_rate']}%")

    print("\nAverage Metrics:")
    print(f"  Avg Gain: {full_data['metrics']['avg_gain']} kr")
    print(f"  Avg Loss: {full_data['metrics']['avg_loss']} kr")
    print(f"  Best Trade: {full_data['metrics']['best_trade']} kr")
    print(f"  Worst Trade: {full_data['metrics']['worst_trade']} kr")

    print(f"\nOpen Positions: {len(full_data['open_positions'])}")
