"""
Alert Scheduler
Scheduled jobs för att kolla positioner och skicka alerts
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
from trade_manager import TradeManager
from stock_data import StockDataFetcher
from user_settings import get_settings
import json
import os
import hashlib

# Severity levels
SEVERITY_CRITICAL = 'CRITICAL'
SEVERITY_HIGH = 'HIGH'
SEVERITY_INFO = 'INFO'

# Alert type to severity mapping
ALERT_SEVERITY = {
    'STOP_LOSS': SEVERITY_CRITICAL,
    'TARGET_1': SEVERITY_HIGH,
    'TARGET_2': SEVERITY_HIGH,
    'TARGET_3': SEVERITY_HIGH,
}

class AlertScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='Europe/Stockholm')
        self.trade_manager = TradeManager()
        self.stock_data = StockDataFetcher()
        self.user_settings = get_settings()
        self.last_check = {
            'SE': None,
            'US': None
        }
        self.alerts_history = self._load_alerts_history()
        self.sent_hashes = self._load_sent_hashes()

    def _load_alerts_history(self):
        """Ladda alert history från fil"""
        history_file = 'alerts_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'alerts': []}

    def _save_alerts_history(self):
        """Spara alert history till fil"""
        with open('alerts_history.json', 'w', encoding='utf-8') as f:
            json.dump(self.alerts_history, f, ensure_ascii=False, indent=2)

    def _add_to_history(self, alert):
        """Lägg till alert i history"""
        alert['timestamp'] = datetime.now().isoformat()
        alert['dismissed'] = False
        self.alerts_history['alerts'].insert(0, alert)  # Senaste först

        # Behåll max 50 alerts
        self.alerts_history['alerts'] = self.alerts_history['alerts'][:50]
        self._save_alerts_history()

    def _load_sent_hashes(self):
        """Ladda skickade alert hashes"""
        hash_file = 'alerts_sent.json'
        if os.path.exists(hash_file):
            with open(hash_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Konvertera timestamps till datetime för cleanup
                return data.get('recent_hashes', {})
        return {}

    def _save_sent_hashes(self):
        """Spara skickade alert hashes"""
        with open('alerts_sent.json', 'w', encoding='utf-8') as f:
            json.dump({'recent_hashes': self.sent_hashes}, f, ensure_ascii=False, indent=2)

    def _get_time_bucket(self, minutes=5, dt=None):
        """
        Få time bucket (rundad ner till närmaste N minuter)

        Args:
            minutes: Bucket size (default 5)
            dt: datetime (default now)

        Returns:
            ISO string rounded down to bucket
        """
        if dt is None:
            dt = datetime.now()

        # Runda ner till närmaste bucket
        bucket_minute = (dt.minute // minutes) * minutes
        bucket_time = dt.replace(minute=bucket_minute, second=0, microsecond=0)

        return bucket_time.isoformat()

    def _generate_alert_hash(self, alert):
        """
        Generera unik hash för alert (för deduplicering)

        Hash format: ticker|type|price_level|time_bucket
        """
        ticker = alert.get('ticker', '')
        alert_type = alert.get('type', '')
        price = alert.get('price', 0)

        # Runda pris till 1 decimal för att undvika micro-variationer
        price_level = f"{float(price):.1f}"

        # 5-minuters bucket
        time_bucket = self._get_time_bucket(minutes=5)

        # Skapa hash-string
        hash_string = f"{ticker}|{alert_type}|{price_level}|{time_bucket}"

        # SHA256 hash
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]

    def _should_send_alert(self, alert):
        """
        Kolla om alert ska skickas (idempotens + quiet hours check)

        Returns:
            True om alert ska skickas
        """
        # 1. Idempotens check
        alert_hash = self._generate_alert_hash(alert)

        if alert_hash in self.sent_hashes:
            # Alert redan skickad inom 5 min
            print(f"  Skippar duplikat: {alert['ticker']} {alert['type']} (hash: {alert_hash})")
            return False

        # 2. Quiet hours check
        alert_type = alert.get('type', '')
        severity = ALERT_SEVERITY.get(alert_type, SEVERITY_INFO)

        if self.user_settings.is_quiet_hours():
            if severity != SEVERITY_CRITICAL and self.user_settings.only_critical_during_quiet_hours():
                print(f"  Skippar non-critical under quiet hours: {alert['ticker']} {alert['type']}")
                # Spara för visning senare
                self._add_to_history(alert)
                return False

        # 3. Markera som skickad
        self.sent_hashes[alert_hash] = datetime.now().isoformat()
        self._save_sent_hashes()

        # 4. Lägg till severity i alert
        alert['severity'] = severity

        return True

    def _cleanup_old_hashes(self):
        """Rensa gamla hashes (äldre än 1 timme)"""
        cutoff = datetime.now() - timedelta(hours=1)

        hashes_to_remove = []
        for hash_key, timestamp_str in self.sent_hashes.items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp < cutoff:
                    hashes_to_remove.append(hash_key)
            except:
                # Invalid timestamp, remove it
                hashes_to_remove.append(hash_key)

        for hash_key in hashes_to_remove:
            del self.sent_hashes[hash_key]

        if hashes_to_remove:
            print(f"  Rensade {len(hashes_to_remove)} gamla alert-hashes")
            self._save_sent_hashes()

    def _is_holiday(self, dt):
        """
        Enkel helgdagscheck (hårdkodade datum)

        TODO: Använd pandas_market_calendars för komplett lista
        """
        year = dt.year
        month = dt.month
        day = dt.day

        # Svenska helgdagar (grundläggande)
        holidays = [
            (1, 1),    # Nyårsdagen
            (1, 6),    # Trettondagen
            (5, 1),    # Första maj
            (6, 6),    # Nationaldagen
            (12, 24),  # Julafton
            (12, 25),  # Juldagen
            (12, 26),  # Annandag jul
            (12, 31),  # Nyårsafton
        ]

        return (month, day) in holidays

    def _is_market_hours(self, market='SE'):
        """Kolla om marknaden är öppen"""
        now = datetime.now(pytz.timezone('Europe/Stockholm'))
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Inte helg
        if weekday >= 5:  # Saturday or Sunday
            return False

        # Inte helgdag
        if self._is_holiday(now):
            return False

        if market == 'SE':
            # Stockholm: 09:00 - 17:30
            if hour < 9:
                return False
            if hour > 17:
                return False
            if hour == 17 and minute > 30:
                return False
            return True

        elif market == 'US':
            # US market: 15:30 - 22:00 CET (09:30 - 16:00 EST)
            if hour < 15:
                return False
            if hour == 15 and minute < 30:
                return False
            if hour >= 22:
                return False
            return True

        return False

    def check_se_positions(self):
        """Kolla svenska positioner"""
        if not self._is_market_hours('SE'):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SE market stängd - skippar check")
            return

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Kollar SE-positioner...")

        try:
            # Cleanup gamla hashes
            self._cleanup_old_hashes()

            # Hämta alla SE-positioner
            se_positions = [p for p in self.trade_manager.positions if p.market == 'SE']

            if not se_positions:
                print("  Inga SE-positioner att kolla")
                return

            # Kolla positioner
            notifications = self.trade_manager.check_positions()

            # Filtrera för SE
            se_notifications = [n for n in notifications if any(
                p.ticker == n['ticker'] and p.market == 'SE'
                for p in self.trade_manager.positions
            )]

            if se_notifications:
                print(f"  {len(se_notifications)} SE-alerts hittade!")

                sent_count = 0
                for notif in se_notifications:
                    # Kolla om alert ska skickas (idempotens + quiet hours)
                    if self._should_send_alert(notif):
                        self._add_to_history(notif)
                        # TODO: Skicka push notification här
                        severity = notif.get('severity', 'INFO')
                        print(f"  -> [{severity}] {notif['type']}: {notif['ticker']} - {notif['action']}")
                        sent_count += 1

                if sent_count > 0:
                    print(f"  Skickade {sent_count}/{len(se_notifications)} alerts")

            self.last_check['SE'] = datetime.now().isoformat()

        except Exception as e:
            print(f"  Fel vid SE-check: {e}")

    def check_us_positions(self):
        """Kolla amerikanska positioner"""
        if not self._is_market_hours('US'):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] US market stängd - skippar check")
            return

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Kollar US-positioner...")

        try:
            # Cleanup gamla hashes
            self._cleanup_old_hashes()

            # Hämta alla US-positioner
            us_positions = [p for p in self.trade_manager.positions if p.market == 'US']

            if not us_positions:
                print("  Inga US-positioner att kolla")
                return

            # Kolla positioner
            notifications = self.trade_manager.check_positions()

            # Filtrera för US
            us_notifications = [n for n in notifications if any(
                p.ticker == n['ticker'] and p.market == 'US'
                for p in self.trade_manager.positions
            )]

            if us_notifications:
                print(f"  {len(us_notifications)} US-alerts hittade!")

                sent_count = 0
                for notif in us_notifications:
                    # Kolla om alert ska skickas (idempotens + quiet hours)
                    if self._should_send_alert(notif):
                        self._add_to_history(notif)
                        # TODO: Skicka push notification här
                        severity = notif.get('severity', 'INFO')
                        print(f"  -> [{severity}] {notif['type']}: {notif['ticker']} - {notif['action']}")
                        sent_count += 1

                if sent_count > 0:
                    print(f"  Skickade {sent_count}/{len(us_notifications)} alerts")

            self.last_check['US'] = datetime.now().isoformat()

        except Exception as e:
            print(f"  Fel vid US-check: {e}")

    def start(self):
        """Starta schedulern"""
        # SE Job: Kör var 3:e minut under svensk marknadstid (09:00-17:30)
        self.scheduler.add_job(
            self.check_se_positions,
            CronTrigger(
                day_of_week='mon-fri',
                hour='9-17',
                minute='*/3',
                timezone='Europe/Stockholm'
            ),
            id='se_position_check',
            name='SE Position Check',
            replace_existing=True
        )

        # US Job: Kör var 3:e minut under amerikansk marknadstid (15:30-22:00 CET)
        self.scheduler.add_job(
            self.check_us_positions,
            CronTrigger(
                day_of_week='mon-fri',
                hour='15-21',
                minute='*/3',
                timezone='Europe/Stockholm'
            ),
            id='us_position_check',
            name='US Position Check',
            replace_existing=True
        )

        self.scheduler.start()
        print("[OK] Alert scheduler startad!")
        print("  - SE-check: Var 3:e min, 09:00-17:30 (man-fre)")
        print("  - US-check: Var 3:e min, 15:30-22:00 (man-fre)")

    def stop(self):
        """Stoppa schedulern"""
        self.scheduler.shutdown()
        print("Alert scheduler stoppad")

    def get_last_check(self, market=None):
        """Hämta senaste check-tidpunkt"""
        if market:
            return self.last_check.get(market)
        return self.last_check

    def get_alerts_history(self, limit=50):
        """Hämta alert history"""
        return self.alerts_history['alerts'][:limit]


# Global scheduler instance
_scheduler_instance = None

def get_scheduler():
    """Hämta global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AlertScheduler()
    return _scheduler_instance
