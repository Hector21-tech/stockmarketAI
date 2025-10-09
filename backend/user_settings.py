"""
User Settings Manager
Hanterar användarinställningar för alerts, quiet hours, etc.
"""

import json
import os
from datetime import datetime


class UserSettings:
    def __init__(self, settings_file='user_settings.json'):
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self):
        """Ladda settings från fil"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Default settings
        return {
            'quiet_hours': {
                'enabled': True,
                'start_hour': 22,  # 22:00
                'end_hour': 8,     # 08:00
                'only_critical': True  # Endast critical alerts under quiet hours
            },
            'base_currency': 'SEK',
            'notifications': {
                'push_enabled': True,
                'email_enabled': False
            }
        }

    def _save_settings(self):
        """Spara settings till fil"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def get_quiet_hours(self):
        """Hämta quiet hours settings"""
        return self.settings.get('quiet_hours', {})

    def is_quiet_hours(self, dt=None):
        """
        Kolla om det är quiet hours

        Args:
            dt: datetime objekt (default: now)

        Returns:
            True om quiet hours är aktiv
        """
        quiet_config = self.get_quiet_hours()

        if not quiet_config.get('enabled', True):
            return False

        if dt is None:
            dt = datetime.now()

        current_hour = dt.hour
        start_hour = quiet_config.get('start_hour', 22)
        end_hour = quiet_config.get('end_hour', 8)

        # Quiet hours kan spänna över midnatt (t.ex. 22:00 - 08:00)
        if start_hour > end_hour:
            # Overnight: 22:00 - 08:00
            return current_hour >= start_hour or current_hour < end_hour
        else:
            # Same day: 08:00 - 22:00
            return start_hour <= current_hour < end_hour

    def only_critical_during_quiet_hours(self):
        """Returnera om endast critical alerts ska skickas under quiet hours"""
        return self.get_quiet_hours().get('only_critical', True)

    def set_quiet_hours(self, enabled=None, start_hour=None, end_hour=None, only_critical=None):
        """Uppdatera quiet hours settings"""
        quiet_config = self.settings.get('quiet_hours', {})

        if enabled is not None:
            quiet_config['enabled'] = enabled
        if start_hour is not None:
            quiet_config['start_hour'] = start_hour
        if end_hour is not None:
            quiet_config['end_hour'] = end_hour
        if only_critical is not None:
            quiet_config['only_critical'] = only_critical

        self.settings['quiet_hours'] = quiet_config
        self._save_settings()

    def get_base_currency(self):
        """Hämta bas-valuta"""
        return self.settings.get('base_currency', 'SEK')

    def set_base_currency(self, currency):
        """Sätt bas-valuta"""
        self.settings['base_currency'] = currency
        self._save_settings()


# Global instance
_settings_instance = None

def get_settings():
    """Hämta global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = UserSettings()
    return _settings_instance
