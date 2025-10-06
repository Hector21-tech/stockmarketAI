"""
Trade Manager - Hanterar positioner och 1/3-exit regeln
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from stock_data import StockDataFetcher

class Position:
    """Representerar en aktieposition"""

    def __init__(self, ticker: str, entry_price: float, shares: int,
                 stop_loss: float, targets: Dict, market: str = "SE"):
        self.ticker = ticker
        self.entry_price = entry_price
        self.initial_shares = shares
        self.current_shares = shares
        self.stop_loss = stop_loss
        self.targets = targets
        self.market = market
        self.entry_date = datetime.now().isoformat()
        self.exits = []  # Lista med exits
        self.status = "OPEN"  # OPEN, PARTIAL, CLOSED

    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'entry_price': self.entry_price,
            'initial_shares': self.initial_shares,
            'current_shares': self.current_shares,
            'stop_loss': self.stop_loss,
            'targets': self.targets,
            'market': self.market,
            'entry_date': self.entry_date,
            'exits': self.exits,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict):
        pos = cls(
            ticker=data['ticker'],
            entry_price=data['entry_price'],
            shares=data['initial_shares'],
            stop_loss=data['stop_loss'],
            targets=data['targets'],
            market=data.get('market', 'SE')
        )
        pos.current_shares = data['current_shares']
        pos.entry_date = data['entry_date']
        pos.exits = data.get('exits', [])
        pos.status = data.get('status', 'OPEN')
        return pos


class TradeManager:
    """
    Hanterar positioner och implementerar Marketmate 1/3-exit regeln
    """

    def __init__(self, positions_file: str = "positions.json"):
        self.positions_file = positions_file
        self.positions: List[Position] = []
        self.fetcher = StockDataFetcher()
        self.load_positions()

    def add_position(self, ticker: str, entry_price: float, shares: int,
                    stop_loss: float, targets: Dict, market: str = "SE") -> Position:
        """
        Lägger till ny position

        Args:
            ticker: Aktiesymbol
            entry_price: Inköpspris
            shares: Antal aktier
            stop_loss: Stop loss nivå
            targets: Dict med target_1, target_2, target_3
            market: Marknad

        Returns:
            Position objekt
        """
        position = Position(ticker, entry_price, shares, stop_loss, targets, market)
        self.positions.append(position)
        self.save_positions()

        print(f"Position tillagd: {ticker} x{shares} @ {entry_price}")
        return position

    def check_positions(self) -> List[Dict]:
        """
        Kollar alla öppna positioner mot targets och stop loss

        Returns:
            Lista med notifikationer/actions
        """
        notifications = []

        for position in self.positions:
            if position.status == "CLOSED":
                continue

            # Hämta nuvarande pris
            current_price = self.fetcher.get_current_price(position.ticker, position.market)

            if not current_price:
                continue

            # Kolla stop loss
            if current_price <= position.stop_loss:
                notification = {
                    'type': 'STOP_LOSS',
                    'ticker': position.ticker,
                    'action': f'Stop loss träffad! Sälj alla {position.current_shares} st @ {current_price}',
                    'price': current_price,
                    'loss_percent': round(((current_price - position.entry_price) / position.entry_price) * 100, 2)
                }
                notifications.append(notification)
                continue

            # Kolla targets (1/3-regeln)
            targets = position.targets

            # Target 1: Första 1/3
            if 'target_1' in targets and position.current_shares == position.initial_shares:
                target_1_price = targets['target_1']['price']

                if current_price >= target_1_price:
                    shares_to_sell = position.initial_shares // 3

                    notification = {
                        'type': 'TARGET_1',
                        'ticker': position.ticker,
                        'action': f'Sälj {shares_to_sell} st @ {current_price} (+{targets["target_1"]["gain_percent"]}%)',
                        'price': current_price,
                        'instruction': 'Flytta stop loss till break-even',
                        'new_stop': position.entry_price
                    }
                    notifications.append(notification)

            # Target 2: Andra 1/3
            elif 'target_2' in targets and position.current_shares == (position.initial_shares * 2 // 3):
                target_2_price = targets['target_2']['price']

                if current_price >= target_2_price:
                    shares_to_sell = position.initial_shares // 3

                    notification = {
                        'type': 'TARGET_2',
                        'ticker': position.ticker,
                        'action': f'Sälj {shares_to_sell} st @ {current_price} (+{targets["target_2"]["gain_percent"]}%)',
                        'price': current_price,
                        'instruction': 'Flytta stop loss under senaste swing-low'
                    }
                    notifications.append(notification)

            # Target 3: Sista 1/3 (håll så länge trend kvarstår)
            elif 'target_3' in targets and position.current_shares == (position.initial_shares // 3):
                target_3_price = targets['target_3']['price']

                if current_price >= target_3_price:
                    notification = {
                        'type': 'TARGET_3',
                        'ticker': position.ticker,
                        'action': f'Överväg att sälja sista {position.current_shares} st @ {current_price}',
                        'price': current_price,
                        'gain_percent': round(((current_price - position.entry_price) / position.entry_price) * 100, 2),
                        'instruction': 'Eller håll så länge trend kvarstår'
                    }
                    notifications.append(notification)

        return notifications

    def execute_exit(self, ticker: str, shares: int, exit_price: float,
                    exit_type: str = "MANUAL") -> bool:
        """
        Registrerar en exit (försäljning)

        Args:
            ticker: Aktiesymbol
            shares: Antal aktier som säljs
            exit_price: Försäljningspris
            exit_type: MANUAL, TARGET_1, TARGET_2, TARGET_3, STOP_LOSS

        Returns:
            True om success
        """
        for position in self.positions:
            if position.ticker == ticker and position.status != "CLOSED":
                if shares > position.current_shares:
                    print(f"Fel: Försöker sälja {shares} men har bara {position.current_shares}")
                    return False

                # Registrera exit
                exit_record = {
                    'shares': shares,
                    'price': exit_price,
                    'type': exit_type,
                    'date': datetime.now().isoformat(),
                    'profit_per_share': round(exit_price - position.entry_price, 2),
                    'profit_percent': round(((exit_price - position.entry_price) / position.entry_price) * 100, 2)
                }

                position.exits.append(exit_record)
                position.current_shares -= shares

                # Uppdatera status
                if position.current_shares == 0:
                    position.status = "CLOSED"
                else:
                    position.status = "PARTIAL"

                self.save_positions()

                print(f"Exit registrerad: {ticker} -{shares} st @ {exit_price} ({exit_type})")
                return True

        return False

    def update_stop_loss(self, ticker: str, new_stop: float) -> bool:
        """
        Uppdaterar stop loss för position

        Args:
            ticker: Aktiesymbol
            new_stop: Ny stop loss nivå

        Returns:
            True om success
        """
        for position in self.positions:
            if position.ticker == ticker and position.status != "CLOSED":
                # Kontrollera att stop inte flyttas nedåt (Marketmate-regel)
                if new_stop < position.stop_loss:
                    print(f"Varning: Stop loss får inte flyttas nedåt! Nuvarande: {position.stop_loss}, Försökt: {new_stop}")
                    return False

                position.stop_loss = new_stop
                self.save_positions()

                print(f"Stop loss uppdaterad för {ticker}: {new_stop}")
                return True

        return False

    def get_open_positions(self) -> List[Position]:
        """Returnerar alla öppna/partiella positioner"""
        return [p for p in self.positions if p.status != "CLOSED"]

    def get_position_summary(self, ticker: str) -> Optional[Dict]:
        """Hämtar sammanfattning av position"""
        for position in self.positions:
            if position.ticker == ticker and position.status != "CLOSED":
                current_price = self.fetcher.get_current_price(position.ticker, position.market)

                if current_price:
                    unrealized_profit = (current_price - position.entry_price) * position.current_shares
                    unrealized_percent = ((current_price - position.entry_price) / position.entry_price) * 100

                    return {
                        'ticker': position.ticker,
                        'current_shares': position.current_shares,
                        'entry_price': position.entry_price,
                        'current_price': current_price,
                        'stop_loss': position.stop_loss,
                        'unrealized_profit': round(unrealized_profit, 2),
                        'unrealized_percent': round(unrealized_percent, 2),
                        'status': position.status,
                        'exits': position.exits
                    }

        return None

    def save_positions(self):
        """Sparar positioner till fil"""
        data = [p.to_dict() for p in self.positions]
        with open(self.positions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_positions(self):
        """Laddar positioner från fil"""
        try:
            with open(self.positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.positions = [Position.from_dict(p) for p in data]
        except FileNotFoundError:
            self.positions = []


# Test
if __name__ == "__main__":
    print("Testing Trade Manager...")
    print("="*60)

    manager = TradeManager("test_positions.json")

    # Exempel: Lägg till position
    targets = {
        'target_1': {'price': 290, 'gain_percent': 4.0},
        'target_2': {'price': 300, 'gain_percent': 7.5},
        'target_3': {'price': 320, 'gain_percent': 15.0}
    }

    manager.add_position(
        ticker="VOLVO-B",
        entry_price=278,
        shares=300,
        stop_loss=270,
        targets=targets,
        market="SE"
    )

    # Kolla positioner
    print("\nKollar positioner...")
    notifications = manager.check_positions()

    for notif in notifications:
        print(f"\n{notif['type']}: {notif['ticker']}")
        print(f"Action: {notif['action']}")

    # Visa öppna positioner
    print("\n\nÖPPNA POSITIONER:")
    for pos in manager.get_open_positions():
        summary = manager.get_position_summary(pos.ticker)
        if summary:
            print(f"\n{summary['ticker']}")
            print(f"Shares: {summary['current_shares']}")
            print(f"Entry: {summary['entry_price']} -> Current: {summary['current_price']}")
            print(f"P/L: {summary['unrealized_profit']} ({summary['unrealized_percent']}%)")
