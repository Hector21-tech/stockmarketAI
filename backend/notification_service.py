"""
Notification Service for MarketsAI
Hanterar push-notifikationer till mobila enheter via Expo Push
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime


class NotificationService:
    """Service for att skicka push-notifikationer"""

    def __init__(self):
        self.expo_push_url = "https://exp.host/--/api/v2/push/send"
        self.push_tokens = {}  # User ID -> Push Token mapping

    def register_push_token(self, user_id: str, push_token: str) -> bool:
        """
        Registrera en push token for en anvandare

        Args:
            user_id: Anvandare ID
            push_token: Expo push token

        Returns:
            bool: True om lyckad
        """
        if not push_token or not push_token.startswith('ExponentPushToken'):
            return False

        self.push_tokens[user_id] = push_token
        return True

    def remove_push_token(self, user_id: str) -> bool:
        """Ta bort push token for en anvandare"""
        if user_id in self.push_tokens:
            del self.push_tokens[user_id]
            return True
        return False

    def send_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "high",
        sound: str = "default"
    ) -> bool:
        """
        Skicka push-notifikation till en enhet

        Args:
            push_token: Expo push token
            title: Notifikationstitel
            body: Notifikationsinnehall
            data: Extra data att skicka med
            priority: high/normal/default
            sound: Ljudnamn

        Returns:
            bool: True om lyckad
        """
        if not push_token or not push_token.startswith('ExponentPushToken'):
            print(f"Invalid push token: {push_token}")
            return False

        message = {
            "to": push_token,
            "title": title,
            "body": body,
            "data": data or {},
            "priority": priority,
            "sound": sound,
            "channelId": "default",
        }

        try:
            response = requests.post(
                self.expo_push_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                data=json.dumps(message)
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('data', {}).get('status') == 'ok':
                    print(f"Notification sent successfully to {push_token[:20]}...")
                    return True
                else:
                    print(f"Notification failed: {result}")
                    return False
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return False

        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False

    def send_bulk_notifications(
        self,
        messages: List[Dict]
    ) -> Dict[str, int]:
        """
        Skicka bulk-notifikationer till flera enheter

        Args:
            messages: Lista med notifikationsmeddelanden

        Returns:
            Dict med success/failed counts
        """
        if not messages:
            return {"success": 0, "failed": 0}

        try:
            response = requests.post(
                self.expo_push_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                data=json.dumps(messages)
            )

            if response.status_code == 200:
                results = response.json().get('data', [])
                success = sum(1 for r in results if r.get('status') == 'ok')
                failed = len(results) - success
                return {"success": success, "failed": failed}
            else:
                return {"success": 0, "failed": len(messages)}

        except Exception as e:
            print(f"Error sending bulk notifications: {str(e)}")
            return {"success": 0, "failed": len(messages)}

    def notify_new_signal(
        self,
        push_token: str,
        ticker: str,
        action: str,
        strength: int,
        reason: str
    ) -> bool:
        """Skicka notifikation om ny trading signal"""
        title = f"📈 Ny Signal: {ticker}"
        body = f"{action} - Styrka: {strength}/10\n{reason}"

        return self.send_notification(
            push_token,
            title,
            body,
            data={
                "type": "signal",
                "ticker": ticker,
                "action": action,
                "strength": strength,
                "timestamp": datetime.now().isoformat()
            }
        )

    def notify_position_update(
        self,
        push_token: str,
        ticker: str,
        profit_loss: float,
        profit_loss_percent: float
    ) -> bool:
        """Skicka notifikation om positionsuppdatering"""
        emoji = "📈" if profit_loss >= 0 else "📉"
        title = f"💰 Position: {ticker}"
        body = f"{emoji} {profit_loss_percent:.2f}% ({profit_loss:.2f} kr)"

        return self.send_notification(
            push_token,
            title,
            body,
            data={
                "type": "position",
                "ticker": ticker,
                "profit_loss": profit_loss,
                "timestamp": datetime.now().isoformat()
            }
        )

    def notify_exit_signal(
        self,
        push_token: str,
        ticker: str,
        reason: str
    ) -> bool:
        """Skicka notifikation om exit signal"""
        title = f"🚪 Exit Signal: {ticker}"

        return self.send_notification(
            push_token,
            title,
            reason,
            data={
                "type": "exit",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat()
            }
        )

    def get_registered_tokens(self) -> Dict[str, str]:
        """Hamta alla registrerade tokens"""
        return self.push_tokens.copy()
