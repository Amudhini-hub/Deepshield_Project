#!/usr/bin/env python3
"""
DeepShield Monitoring and Metrics Setup
Provides observability, metrics collection, and alerting
"""

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import requests

logger = logging.getLogger(__name__)

# Import alerting for system checks
try:
    from .alerting import check_system_alerts
except ImportError:
    # Fallback if alerting module not available
    check_system_alerts = lambda x: []


@dataclass
class SystemMetrics:
    """System resource metrics"""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_connections: int


@dataclass
class APIMetrics:
    """API performance metrics"""

    timestamp: str
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    user_id: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class SecurityMetrics:
    """Security-related metrics"""

    timestamp: str
    event_type: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    risk_score: Optional[float] = None
    action_taken: Optional[str] = None


class MetricsCollector:
    """Collects and manages system and application metrics"""

    def __init__(self, metrics_dir: str = "metrics", retention_days: int = 30):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        self.retention_days = retention_days

        # Metrics storage
        self.system_metrics: List[SystemMetrics] = []
        self.api_metrics: List[APIMetrics] = []
        self.security_metrics: List[SecurityMetrics] = []

        # Start background collection
        self.collection_thread = threading.Thread(
            target=self._background_collection, daemon=True
        )
        self.collection_thread.start()

        logger.info("Metrics collector initialized")

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # Network
            network_connections = len(psutil.net_connections())

            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_connections=network_connections,
            )

            self.system_metrics.append(metrics)
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None

    def record_api_metrics(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """Record API call metrics"""
        try:
            metrics = APIMetrics(
                timestamp=datetime.now().isoformat(),
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time_ms,
                status_code=status_code,
                user_id=user_id,
                error_type=error_type,
            )

            self.api_metrics.append(metrics)

            # Log slow requests
            if response_time_ms > 1000:  # 1 second
                logger.warning(
                    f"Slow API request: {endpoint} took {response_time_ms:.2f}ms"
                )

            # Log errors
            if status_code >= 400:
                logger.warning(f"API error: {endpoint} returned {status_code}")

        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")

    def record_security_metrics(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        risk_score: Optional[float] = None,
        action_taken: Optional[str] = None,
    ):
        """Record security event metrics"""
        try:
            metrics = SecurityMetrics(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                risk_score=risk_score,
                action_taken=action_taken,
            )

            self.security_metrics.append(metrics)

            # Log high-risk events
            if risk_score and risk_score > 0.8:
                logger.warning(
                    f"High-risk security event: {event_type} for user {user_id}"
                )

        except Exception as e:
            logger.error(f"Failed to record security metrics: {e}")

    def _background_collection(self):
        """Background system metrics collection"""
        while True:
            try:
                metrics = self.collect_system_metrics()

                # Check for alerts based on system metrics
                if metrics:
                    metrics_data = asdict(metrics)
                    check_system_alerts(metrics_data)

                # Also check API metrics for alerts
                api_stats = self.get_api_stats(hours=1)  # Last hour
                if api_stats.get("total_requests", 0) > 0:
                    check_system_alerts(api_stats)

                # Check security metrics for alerts
                security_stats = self.get_security_stats(hours=1)  # Last hour
                if security_stats.get("total_events", 0) > 0:
                    check_system_alerts(security_stats)

                self._cleanup_old_metrics()

                # Save metrics every 5 minutes
                if len(self.system_metrics) % 5 == 0:
                    self._save_metrics_to_file()

            except Exception as e:
                logger.error(f"Background collection error: {e}")

            time.sleep(60)  # Collect every minute

    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        # Clean system metrics
        self.system_metrics = [
            m
            for m in self.system_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]

        # Clean API metrics
        self.api_metrics = [
            m
            for m in self.api_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]

        # Clean security metrics
        self.security_metrics = [
            m
            for m in self.security_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]

    def _save_metrics_to_file(self):
        """Save metrics to JSON files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save system metrics
            if self.system_metrics:
                system_file = self.metrics_dir / f"system_metrics_{timestamp}.json"
                with open(system_file, "w") as f:
                    json.dump(
                        [asdict(m) for m in self.system_metrics[-100:]], f, indent=2
                    )

            # Save API metrics
            if self.api_metrics:
                api_file = self.metrics_dir / f"api_metrics_{timestamp}.json"
                with open(api_file, "w") as f:
                    json.dump([asdict(m) for m in self.api_metrics[-500:]], f, indent=2)

            # Save security metrics
            if self.security_metrics:
                security_file = self.metrics_dir / f"security_metrics_{timestamp}.json"
                with open(security_file, "w") as f:
                    json.dump(
                        [asdict(m) for m in self.security_metrics[-200:]], f, indent=2
                    )

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def get_system_health(self) -> Dict:
        """Get current system health status"""
        if not self.system_metrics:
            return {"status": "unknown", "message": "No metrics available"}

        latest = self.system_metrics[-1]

        # Define health thresholds
        health_status = "healthy"
        issues = []

        if latest.cpu_percent > 90:
            health_status = "critical"
            issues.append("High CPU usage")
        elif latest.cpu_percent > 70:
            health_status = "warning"
            issues.append("Elevated CPU usage")

        if latest.memory_percent > 90:
            health_status = "critical"
            issues.append("High memory usage")
        elif latest.memory_percent > 80:
            health_status = "warning"
            issues.append("Elevated memory usage")

        if latest.disk_usage_percent > 95:
            health_status = "critical"
            issues.append("Low disk space")
        elif latest.disk_usage_percent > 85:
            health_status = "warning"
            issues.append("Low disk space")

        return {
            "status": health_status,
            "timestamp": latest.timestamp,
            "issues": issues,
            "metrics": asdict(latest),
        }

    def get_api_stats(self, hours: int = 24) -> Dict:
        """Get API performance statistics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter recent metrics
        recent_metrics = [
            m
            for m in self.api_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not recent_metrics:
            return {"total_requests": 0, "message": "No API metrics available"}

        # Calculate statistics
        total_requests = len(recent_metrics)
        avg_response_time = (
            sum(m.response_time_ms for m in recent_metrics) / total_requests
        )

        status_counts = {}
        for m in recent_metrics:
            status_counts[m.status_code] = status_counts.get(m.status_code, 0) + 1

        error_rate = (
            sum(1 for m in recent_metrics if m.status_code >= 400)
            / total_requests
            * 100
        )

        # Endpoint performance
        endpoint_stats = {}
        for m in recent_metrics:
            key = f"{m.method} {m.endpoint}"
            if key not in endpoint_stats:
                endpoint_stats[key] = {"count": 0, "total_time": 0}
            endpoint_stats[key]["count"] += 1
            endpoint_stats[key]["total_time"] += m.response_time_ms

        for key in endpoint_stats:
            endpoint_stats[key]["avg_time"] = (
                endpoint_stats[key]["total_time"] / endpoint_stats[key]["count"]
            )

        return {
            "total_requests": total_requests,
            "avg_response_time_ms": avg_response_time,
            "error_rate_percent": error_rate,
            "status_codes": status_counts,
            "endpoint_performance": endpoint_stats,
            "time_range_hours": hours,
        }

    def get_security_stats(self, hours: int = 24) -> Dict:
        """Get security event statistics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter recent metrics
        recent_metrics = [
            m
            for m in self.security_metrics
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not recent_metrics:
            return {"total_events": 0, "message": "No security metrics available"}

        # Event type counts
        event_counts = {}
        for m in recent_metrics:
            event_counts[m.event_type] = event_counts.get(m.event_type, 0) + 1

        # Risk score distribution
        risk_scores = [m.risk_score for m in recent_metrics if m.risk_score is not None]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        # High-risk events
        high_risk_events = sum(
            1 for m in recent_metrics if m.risk_score and m.risk_score > 0.7
        )

        return {
            "total_events": len(recent_metrics),
            "event_types": event_counts,
            "avg_risk_score": avg_risk_score,
            "high_risk_events": high_risk_events,
            "time_range_hours": hours,
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector


def record_api_call(
    endpoint: str,
    method: str,
    response_time_ms: float,
    status_code: int,
    user_id: Optional[str] = None,
    error_type: Optional[str] = None,
):
    """Convenience function to record API metrics"""
    metrics_collector.record_api_metrics(
        endpoint, method, response_time_ms, status_code, user_id, error_type
    )


def record_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    risk_score: Optional[float] = None,
    action_taken: Optional[str] = None,
):
    """Convenience function to record security metrics"""
    metrics_collector.record_security_metrics(
        event_type, user_id, ip_address, user_agent, risk_score, action_taken
    )


def get_system_health() -> Dict:
    """Get current system health"""
    return metrics_collector.get_system_health()


def get_api_stats(hours: int = 24) -> Dict:
    """Get API performance statistics"""
    return metrics_collector.get_api_stats(hours)


def get_security_stats(hours: int = 24) -> Dict:
    """Get security event statistics"""
    return metrics_collector.get_security_stats(hours)
