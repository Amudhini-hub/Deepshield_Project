#!/usr/bin/env python3
"""
DeepShield Alerting System
Provides configurable alerts for system health, performance, and security events
"""

import json
import logging
import smtplib
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    condition: str  # Python expression to evaluate
    threshold: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    cooldown_minutes: int = 5
    enabled: bool = True
    description: str = ""


@dataclass
class Alert:
    """Alert instance"""

    rule_name: str
    severity: str
    message: str
    timestamp: str
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[str] = None


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(
        self, config_file: str = "alerts_config.json", alerts_dir: str = "alerts"
    ):
        self.config_file = Path(config_file)
        self.alerts_dir = Path(alerts_dir)
        self.alerts_dir.mkdir(exist_ok=True)

        # Alert state
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Notification settings
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_email": "",
            "to_emails": [],
        }

        self.slack_webhook = ""
        self.telegram_bot_token = ""
        self.telegram_chat_id = ""

        # Default alert rules
        self.alert_rules = self._get_default_rules()

        # Load configuration
        self._load_config()

        # Start alert monitoring
        self.monitoring_thread = threading.Thread(
            target=self._monitor_alerts, daemon=True
        )
        self.monitoring_thread.start()

        logger.info("Alert manager initialized")

    def _get_default_rules(self) -> Dict[str, AlertRule]:
        """Get default alert rules"""
        return {
            "high_cpu": AlertRule(
                name="high_cpu",
                condition="cpu_percent > threshold",
                threshold=90.0,
                severity="high",
                cooldown_minutes=10,
                description="CPU usage exceeds threshold",
            ),
            "high_memory": AlertRule(
                name="high_memory",
                condition="memory_percent > threshold",
                threshold=85.0,
                severity="high",
                cooldown_minutes=10,
                description="Memory usage exceeds threshold",
            ),
            "low_disk_space": AlertRule(
                name="low_disk_space",
                condition="disk_usage_percent > threshold",
                threshold=90.0,
                severity="critical",
                cooldown_minutes=60,
                description="Disk space is critically low",
            ),
            "high_error_rate": AlertRule(
                name="high_error_rate",
                condition="error_rate_percent > threshold",
                threshold=10.0,
                severity="medium",
                cooldown_minutes=15,
                description="API error rate exceeds threshold",
            ),
            "slow_response_time": AlertRule(
                name="slow_response_time",
                condition="avg_response_time_ms > threshold",
                threshold=2000.0,
                severity="medium",
                cooldown_minutes=5,
                description="Average API response time is too slow",
            ),
            "high_risk_events": AlertRule(
                name="high_risk_events",
                condition="high_risk_events > threshold",
                threshold=5,
                severity="high",
                cooldown_minutes=30,
                description="High number of security risk events detected",
            ),
        }

    def _load_config(self):
        """Load alert configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)

                # Load email config
                if "email" in config:
                    self.email_config.update(config["email"])

                # Load webhook configs
                if "slack_webhook" in config:
                    self.slack_webhook = config["slack_webhook"]

                if "telegram" in config:
                    self.telegram_bot_token = config["telegram"].get("bot_token", "")
                    self.telegram_chat_id = config["telegram"].get("chat_id", "")

                # Load custom rules
                if "custom_rules" in config:
                    for rule_data in config["custom_rules"]:
                        rule = AlertRule(**rule_data)
                        self.alert_rules[rule.name] = rule

                logger.info("Alert configuration loaded")

        except Exception as e:
            logger.error(f"Failed to load alert config: {e}")

    def _save_config(self):
        """Save alert configuration to file"""
        try:
            config = {
                "email": self.email_config,
                "slack_webhook": self.slack_webhook,
                "telegram": {
                    "bot_token": self.telegram_bot_token,
                    "chat_id": self.telegram_chat_id,
                },
                "custom_rules": [
                    {k: v for k, v in rule.__dict__.items()}
                    for rule in self.alert_rules.values()
                    if rule.name not in self._get_default_rules()
                ],
            }

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save alert config: {e}")

    def add_custom_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.alert_rules[rule.name] = rule
        self._save_config()
        logger.info(f"Added custom alert rule: {rule.name}")

    def update_rule_threshold(self, rule_name: str, threshold: float):
        """Update threshold for an alert rule"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].threshold = threshold
            self._save_config()
            logger.info(f"Updated threshold for {rule_name}: {threshold}")

    def enable_rule(self, rule_name: str, enabled: bool = True):
        """Enable or disable an alert rule"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = enabled
            self._save_config()
            logger.info(
                f"{'Enabled' if enabled else 'Disabled'} alert rule: {rule_name}"
            )

    def check_alerts(self, metrics_data: Dict):
        """Check all alert rules against current metrics"""
        triggered_alerts = []

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            try:
                # Evaluate condition
                condition_met = self._evaluate_condition(
                    rule.condition, metrics_data, rule.threshold
                )

                if condition_met:
                    # Check cooldown
                    if self._should_trigger_alert(rule.name, rule.cooldown_minutes):
                        alert = Alert(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=f"{rule.description}: {self._get_metric_value(metrics_data, rule.condition)}",
                            timestamp=datetime.now().isoformat(),
                            value=self._get_metric_value(metrics_data, rule.condition),
                            threshold=rule.threshold,
                        )

                        self.active_alerts[rule.name] = alert
                        self.alert_history.append(alert)
                        triggered_alerts.append(alert)

                        logger.warning(
                            f"Alert triggered: {rule.name} - {alert.message}"
                        )

            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}: {e}")

        return triggered_alerts

    def _evaluate_condition(
        self, condition: str, metrics: Dict, threshold: float
    ) -> bool:
        """Evaluate alert condition expression"""
        # Simple condition evaluation - in production, use a safer expression evaluator
        try:
            # Extract metric name from condition (e.g., "cpu_percent > threshold")
            metric_name = condition.split()[0]
            operator = condition.split()[1]

            if metric_name in metrics:
                value = metrics[metric_name]
                if operator == ">":
                    return value > threshold
                elif operator == "<":
                    return value < threshold
                elif operator == ">=":
                    return value >= threshold
                elif operator == "<=":
                    return value <= threshold

        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}")

        return False

    def _get_metric_value(self, metrics: Dict, condition: str) -> float:
        """Extract metric value from condition"""
        try:
            metric_name = condition.split()[0]
            return metrics.get(metric_name, 0.0)
        except:
            return 0.0

    def _should_trigger_alert(self, rule_name: str, cooldown_minutes: int) -> bool:
        """Check if alert should be triggered based on cooldown"""
        if rule_name not in self.active_alerts:
            return True

        last_alert = self.active_alerts[rule_name]
        last_alert_time = datetime.fromisoformat(last_alert.timestamp)
        cooldown_period = timedelta(minutes=cooldown_minutes)

        return datetime.now() - last_alert_time > cooldown_period

    def resolve_alert(self, rule_name: str):
        """Resolve an active alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_at = datetime.now().isoformat()

            logger.info(f"Alert resolved: {rule_name}")

    def _monitor_alerts(self):
        """Background monitoring for alerts"""
        while True:
            try:
                # This would be called periodically with current metrics
                # For now, just sleep
                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                time.sleep(60)

    def send_notifications(self, alerts: List[Alert]):
        """Send notifications for triggered alerts"""
        for alert in alerts:
            try:
                self._send_email_alert(alert)
                self._send_slack_alert(alert)
                self._send_telegram_alert(alert)

            except Exception as e:
                logger.error(
                    f"Failed to send notification for alert {alert.rule_name}: {e}"
                )

    def _send_email_alert(self, alert: Alert):
        """Send email notification"""
        if not self.email_config["to_emails"]:
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["from_email"]
            msg["To"] = ", ".join(self.email_config["to_emails"])
            msg["Subject"] = (
                f"DeepShield Alert: {alert.severity.upper()} - {alert.rule_name}"
            )

            body = f"""
DeepShield Security Alert

Severity: {alert.severity.upper()}
Rule: {alert.rule_name}
Message: {alert.message}
Value: {alert.value}
Threshold: {alert.threshold}
Time: {alert.timestamp}

Please check the system immediately.
            """

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            )
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.sendmail(
                self.email_config["from_email"],
                self.email_config["to_emails"],
                msg.as_string(),
            )
            server.quit()

            logger.info(f"Email alert sent for {alert.rule_name}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _send_slack_alert(self, alert: Alert):
        """Send Slack notification"""
        if not self.slack_webhook:
            return

        try:
            payload = {
                "text": f":warning: *DeepShield Alert*\n*Severity:* {alert.severity.upper()}\n*Rule:* {alert.rule_name}\n*Message:* {alert.message}\n*Time:* {alert.timestamp}",
                "username": "DeepShield Monitor",
                "icon_emoji": ":shield:",
            }

            response = requests.post(self.slack_webhook, json=payload)
            response.raise_for_status()

            logger.info(f"Slack alert sent for {alert.rule_name}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _send_telegram_alert(self, alert: Alert):
        """Send Telegram notification"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return

        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            message = f"""
🚨 *DeepShield Alert*

*Severity:* {alert.severity.upper()}
*Rule:* {alert.rule_name}
*Message:* {alert.message}
*Value:* {alert.value}
*Threshold:* {alert.threshold}
*Time:* {alert.timestamp}
            """.strip()

            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, json=payload)
            response.raise_for_status()

            logger.info(f"Telegram alert sent for {alert.rule_name}")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        return [alert.__dict__ for alert in self.active_alerts.values()]

    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert.__dict__
            for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp) > cutoff_time
        ]


# Global alert manager instance
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance"""
    return alert_manager


def check_system_alerts(metrics_data: Dict):
    """Check system metrics against alert rules"""
    alerts = alert_manager.check_alerts(metrics_data)
    if alerts:
        alert_manager.send_notifications(alerts)
    return alerts
