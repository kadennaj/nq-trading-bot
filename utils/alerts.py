"""
Alert System - Zo Native
Sends SMS via Zo's API from trading bot
"""

import logging
import os
import requests
import subprocess
import sys

logger = logging.getLogger(__name__)


class AlertManager:
    """Sends alerts via Zo's SMS system."""
    
    def __init__(self, enable_sms: bool = True, enable_email: bool = False):
        self.enable_sms = enable_sms
        self.enable_email = enable_email
        self.zo_token = os.environ.get('ZO_CLIENT_IDENTITY_TOKEN', '')
        logger.info("Alert manager initialized - using Zo SMS")
    
    def send_trade_signal(self, signal: dict, entry_price: float):
        """Send alert when trade signal is generated."""
        if not self.enable_sms:
            return
        
        action = signal.get('action', 'UNKNOWN').upper()
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)
        
        msg = f"🔔 NQ TRADE SIGNAL\n"
        msg += f"Action: {action}\n"
        msg += f"Entry: {entry_price:.2f}\n"
        msg += f"SL: {stop_loss:.2f} | TP: {take_profit:.2f}"
        
        self._send_sms(msg)
    
    def send_trade_execution(self, trade: dict):
        """Send alert when trade is executed."""
        if not self.enable_sms:
            return
        
        action = trade.get('action', 'UNKNOWN').upper()
        entry = trade.get('entry_price', 0)
        
        msg = f"✅ NQ TRADE EXECUTED\n"
        msg += f"{action} @ {entry:.2f}"
        
        self._send_sms(msg)
    
    def send_trade_close(self, trade: dict):
        """Send alert when trade is closed."""
        if not self.enable_sms:
            return
        
        pnl = trade.get('pnl', 0)
        reason = trade.get('exit_reason', 'unknown')
        
        emoji = "✅" if pnl > 0 else "❌"
        msg = f"{emoji} NQ TRADE CLOSED\n"
        msg += f"PnL: {pnl:.2f} pts\n"
        msg += f"Reason: {reason}"
        
        self._send_sms(msg)
    
    def _send_sms(self, message: str):
        """Send SMS via Zo API."""
        logger.info(f"ALERT: {message}")
        
        if not self.zo_token:
            logger.warning("No ZO_CLIENT_IDENTITY_TOKEN found, skipping SMS")
            return
        
        try:
            # Use Zo's SMS API
            response = requests.post(
                "https://api.zo.com/zo/sms",
                headers={
                    "Authorization": f"Bearer {self.zo_token}",
                    "Content-Type": "application/json"
                },
                json={"message": message},
                timeout=10
            )
            if response.status_code == 200:
                logger.info("SMS sent successfully")
            else:
                logger.warning(f"SMS failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"SMS error: {e}")


def create_alert_manager(enable_sms: bool = True, enable_email: bool = False) -> AlertManager:
    """Factory function to create AlertManager."""
    return AlertManager(enable_sms=enable_sms, enable_email=enable_email)
