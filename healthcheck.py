"""
Healthcheck System - Monitors bot health
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

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
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._update_metric(
                name="cpu_usage",
                value=cpu_percent,
                unit="%",
                threshold_warning=80,
                threshold_critical=95
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self._update_metric(
                name="memory_usage",
                value=memory_percent,
                unit="%",
                threshold_warning=85,
                threshold_critical=95
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self._update_metric(
                name="disk_usage",
                value=disk_percent,
                unit="%",
                threshold_warning=90,
                threshold_critical=98
            )
            
            # Bot process info
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self._update_metric(
                name="bot_memory",
                value=memory_mb,
                unit="MB",
                threshold_warning=512,  # 512MB
                threshold_critical=1024  # 1GB
            )
            
        except Exception as e:
            self.logger.error(f"❌ System metrics error: {e}")
            
    async def _check_bot_metrics(self):
        """Check bot-specific metrics"""
        try:
            # Get bot metrics from other components
            # These would be populated by other systems
            
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
                # TODO: Actually check each service
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
            
        # Check for critical metrics
        for metric in self.metrics.values():
            if metric.status == HealthStatus.CRITICAL:
                return HealthStatus.CRITICAL
                
        # Check for warning metrics
        for metric in self.metrics.values():
            if metric.status == HealthStatus.WARNING:
                return HealthStatus.WARNING
                
        # Check services
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
            'metrics': {},
            'services': {},
            'system_info': self._get_system_info(),
            'history_summary': self._get_history_summary()
        }
        
        # Add metrics
        for name, metric in self.metrics.items():
            report['metrics'][name] = {
                'value': metric.value,
                'unit': metric.unit,
                'status': metric.status.value,
                'threshold_warning': metric.threshold_warning,
                'threshold_critical': metric.threshold_critical
            }
            
        # Add services
        for name, service in self.services.items():
            report['services'][name] = {
                'status': service.status.value,
                'uptime': service.uptime,
                'error_count': service.error_count,
                'response_time': service.response_time
            }
            
        return report
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform,
                'processor': psutil.cpu_count(),
                'total_memory_gb': psutil.virtual_memory().total / (1024**3),
                'total_disk_gb': psutil.disk_usage('/').total / (1024**3)
            }
        except:
            return {}
            
    def _get_history_summary(self) -> Dict[str, Any]:
        """Get health history summary"""
        if not self.health_history:
            return {}
            
        last_24h = [h for h in self.health_history 
                   if time.time() - datetime.fromisoformat(h['timestamp']).timestamp() < 86400]
                   
        status_counts = {}
        for record in last_24h:
            status = record['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            'total_checks_24h': len(last_24h),
            'status_distribution': status_counts,
            'last_check': self.health_history[-1]['timestamp'] if self.health_history else None
        }
        
    def register_service(self, name: str):
        """Register a service for monitoring"""
        if name not in self.services:
            self.services[name] = ServiceStatus(
                name=name,
                status=HealthStatus.HEALTHY,
                uptime=0,
                last_check=0,
                error_count=0,
                response_time=0
            )
            
    def update_service_status(self, name: str, status: HealthStatus, 
                            response_time: float = 0):
        """Update service status"""
        if name in self.services:
            service = self.services[name]
            service.status = status
            service.last_check = time.time()
            service.response_time = response_time
            
            if status != HealthStatus.HEALTHY:
                service.error_count += 1
                
    def get_service_status(self, name: str) -> Optional[ServiceStatus]:
        """Get service status by name"""
        return self.services.get(name)
        
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self._calculate_overall_status() == HealthStatus.HEALTHY
        
    def trigger_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Trigger health alert"""
        self.logger.warning(f"🚨 Health Alert [{severity}]: {message}")
        
        # TODO: Send notification to admins
        # TODO: Log to health alerts file