"""
Alert System
Sends SMS notifications for trading signals via Twilio
"""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class AlertManager:
    """Manages alerts for trading signals."""
    
    def __init__(self, enable_sms: bool = True, enable_email: bool = True):
        self.logger = logging.getLogger(__name__)
        self.enable_sms = enable_sms
        self.enable_email = enable_email
        
        # Twilio credentials from environment
        self.twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER', '')
        self.my_phone = os.environ.get('MY_PHONE_NUMBER', '')
        
        if self.twilio_sid and self.twilio_token:
            from twilio.rest import Client
            self.twilio_client = Client(self.twilio_sid, self.twilio_token)
        else:
            self.twilio_client = None
            self.logger.warning("Twilio not configured - SMS alerts disabled")
    
    def send_trade_signal(self, signal: dict, current_price: float):
        """Send alert for new trade signal."""
        action = signal['action'].upper()
        entry = signal.get('entry_price', current_price)
        stop = signal.get('stop_loss', 'N/A')
        tp = signal.get('take_profit', 'N/A')
        
        message = (
            f"🚨 NQ TRADE SIGNAL\n"
            f"Action: {action}\n"
            f"Entry: {entry:.2f}\n"
            f"Stop: {stop}\n"
            f"TP: {tp}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if self.enable_sms:
            self._send_sms(message)
    
    def send_trade_update(self, trade: dict):
        """Send alert for trade exit."""
        action = trade.get('action', 'UNKNOWN').upper()
        pnl = trade.get('pnl', 0)
        exit_reason = trade.get('exit_reason', 'unknown')
        
        emoji = "✅" if pnl > 0 else "❌"
        
        message = (
            f"{emoji} NQ TRADE CLOSED\n"
            f"Action: {action}\n"
            f"PnL: {pnl:.2f} pts\n"
            f"Exit: {exit_reason}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if self.enable_sms:
            self._send_sms(message)
    
    def _send_sms(self, message: str):
        """Send SMS via Twilio."""
        if not self.twilio_client or not self.my_phone:
            self.logger.warning(f"SMS not configured. Message: {message}")
            return
        
        try:
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.my_phone
            )
            self.logger.info(f"SMS sent: {message[:50]}...")
        except Exception as e:
            self.logger.error(f"Failed to send SMS: {e}")


def create_alert_manager(enable_sms: bool = True, enable_email: bool = True) -> AlertManager:
    """Factory function to create AlertManager."""
    return AlertManager(enable_sms=enable_sms, enable_email=enable_email)
