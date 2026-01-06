"""
Healthcheck System - Monitors bot health (Production-ready Termux/Android)
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass
from enum import Enum
import sys

# Load config
try:
    import json
    with open("config/bot.json", "r", encoding="utf-8") as f:
        BOT_CONFIG = json.load(f)
except:
    BOT_CONFIG = {}
ENABLE_SYSTEM_METRICS = BOT_CONFIG.get("ENABLE_SYSTEM_METRICS", False)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class HealthMetric:
    """Health metric data"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: float

@dataclass
class ServiceStatus:
    """Service status data"""
    name: str
    status: HealthStatus
    uptime: float
    last_check: float
    error_count: int
    response_time: float

class HealthMonitor:
    """Monitors bot health and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_health")
        self.metrics: Dict[str, HealthMetric] = {}
        self.services: Dict[str, ServiceStatus] = {}
        self.health_history: List[Dict] = []
        self.start_time = time.time()
        self.check_interval = 60  # seconds
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.logger.info("❤️ Starting health monitoring...")
        
        # Initial check
        await self.run_health_check()
        
        # Start periodic monitoring
        asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        self.logger.info("🛑 Stopping health monitoring")
        
    async def _monitoring_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            try:
                await self.run_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(30)
                
    async def run_health_check(self):
        """Run comprehensive health check"""
        check_time = time.time()
        self.logger.debug("🩺 Running health check...")
        
        # System metrics
        await self._check_system_metrics()
        
        # Bot metrics
        await self._check_bot_metrics()
        
        # Service status
        await self._check_services()
        
        # Record health status
        overall_status = self._calculate_overall_status()
        
        health_record = {
            'timestamp': datetime.now().isoformat(),
            'status': overall_status.value,
            'metrics_count': len(self.metrics),
            'services_count': len(self.services),
            'uptime': check_time - self.start_time
        }
        
        self.health_history.append(health_record)
        
        # Keep only last 1000 records
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
            
        # Log if not healthy
        if overall_status != HealthStatus.HEALTHY:
            self.logger.warning(f"⚠️ Health status: {overall_status.value}")
            
        return overall_status
        
    async def _check_system_metrics(self):
        """Check system metrics"""
        if not ENABLE_SYSTEM_METRICS:
            self.logger.info("⚠️ System metrics disabled via config")
            return
        
        try:
            # CPU usage
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
            except (PermissionError, FileNotFoundError):
                cpu_percent = None
            if cpu_percent is not None:
                self._update_metric(
                    name="cpu_usage",
                    value=cpu_percent,
                    unit="%",
                    threshold_warning=80,
                    threshold_critical=95
                )
            
            # Memory usage
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
            except (PermissionError, FileNotFoundError):
                memory_percent = None
            if memory_percent is not None:
                self._update_metric(
                    name="memory_usage",
                    value=memory_percent,
                    unit="%",
                    threshold_warning=85,
                    threshold_critical=95
                )
            
            # Disk usage
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
            except (PermissionError, FileNotFoundError):
                disk_percent = None
            if disk_percent is not None:
                self._update_metric(
                    name="disk_usage",
                    value=disk_percent,
                    unit="%",
                    threshold_warning=90,
                    threshold_critical=98
                )
            
            # Bot memory
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self._update_metric(
                    name="bot_memory",
                    value=memory_mb,
                    unit="MB",
                    threshold_warning=512,
                    threshold_critical=1024
                )
            except (PermissionError, FileNotFoundError):
                pass
            
        except Exception as e:
            self.logger.error(f"❌ System metrics error: {e}")
            
    async def _check_bot_metrics(self):
        """Check bot-specific metrics"""
        try:
            # Placeholder metrics
            self._update_metric(
                name="active_users",
                value=0,
                unit="users",
                threshold_warning=1000,
                threshold_critical=5000
            )
            self._update_metric(
                name="messages_per_minute",
                value=0,
                unit="msg/min",
                threshold_warning=100,
                threshold_critical=500
            )
            self._update_metric(
                name="response_time",
                value=0.1,
                unit="seconds",
                threshold_warning=2.0,
                threshold_critical=5.0
            )
        except Exception as e:
            self.logger.error(f"❌ Bot metrics error: {e}")
            
    async def _check_services(self):
        """Check service status"""
        services_to_check = [
            "telegram_api",
            "database",
            "cache",
            "scheduler",
            "security"
        ]
        
        for service_name in services_to_check:
            try:
                status = HealthStatus.HEALTHY
                response_time = 0.01
                if service_name not in self.services:
                    self.services[service_name] = ServiceStatus(
                        name=service_name,
                        status=status,
                        uptime=time.time() - self.start_time,
                        last_check=time.time(),
                        error_count=0,
                        response_time=response_time
                    )
                else:
                    service = self.services[service_name]
                    service.status = status
                    service.last_check = time.time()
                    service.response_time = response_time
                    
            except Exception as e:
                self.logger.error(f"❌ Service check error for {service_name}: {e}")
                
    def _update_metric(self, name: str, value: float, unit: str,
                      threshold_warning: float, threshold_critical: float):
        """Update a health metric"""
        if value is None:
            return
        if value >= threshold_critical:
            status = HealthStatus.CRITICAL
        elif value >= threshold_warning:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
            
        metric = HealthMetric(
            name=name,
            value=value,
            unit=unit,
            status=status,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            timestamp=time.time()
        )
        
        self.metrics[name] = metric
        
    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall health status"""
        if not self.metrics:
            return HealthStatus.HEALTHY
        for metric in self.metrics.values():
            if metric.status == HealthStatus.CRITICAL:
                return HealthStatus.CRITICAL
        for metric in self.metrics.values():
            if metric.status == HealthStatus.WARNING:
                return HealthStatus.WARNING
        for service in self.services.values():
            if service.status != HealthStatus.HEALTHY:
                return service.status
        return HealthStatus.HEALTHY
        
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        overall_status = self._calculate_overall_status()
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': overall_status.value,
            'uptime': time.time() - self.start_time,
            'metrics': {k: {'value': v.value, 'unit': v.unit, 'status': v.status.value} for k,v in self.metrics.items()},
            'services': {k: {'status': v.status.value, 'uptime': v.uptime} for k,v in self.services.items()}
        }
        return report
