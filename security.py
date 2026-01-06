"""
Security System - Handles security and protection
"""

import re
import logging
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import hashlib
import secrets
from dataclasses import dataclass

@dataclass
class SecurityAlert:
    """Security alert data"""
    alert_id: str
    alert_type: str
    severity: int  # 1-10
    message: str
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    timestamp: float = None
    data: Dict = None

@dataclass
class ThreatDetection:
    """Threat detection result"""
    is_threat: bool
    threat_level: int
    reasons: List[str]
    action: str = "monitor"  # monitor, warn, mute, ban

class SecuritySystem:
    """Main security system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_security")
        self.alerts: List[SecurityAlert] = []
        self.blacklist: Set[int] = set()
        self.suspicious_users: Dict[int, Dict] = {}
        self.threat_patterns = self._load_threat_patterns()
        self.rate_limits: Dict[str, Dict] = {}
        
    def _load_threat_patterns(self) -> Dict[str, re.Pattern]:
        """Load threat detection patterns"""
        patterns = {
            'spam': re.compile(r'(.)\1{5,}'),  # Repeated characters
            'caps': re.compile(r'[A-Z]{10,}'),  # Excessive caps
            'links': re.compile(r'https?://\S+'),
            'phone': re.compile(r'\b\d{11,}\b'),  # Phone numbers
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        }
        return patterns
        
    async def analyze_message(self, user_id: int, message: str, 
                            group_id: Optional[int] = None) -> ThreatDetection:
        """
        Analyze message for threats
        
        Args:
            user_id: User ID
            message: Message text
            group_id: Group ID
            
        Returns:
            Threat detection result
        """
        threats = []
        threat_level = 0
        
        # Check blacklist
        if user_id in self.blacklist:
            return ThreatDetection(
                is_threat=True,
                threat_level=10,
                reasons=["User is blacklisted"],
                action="ban"
            )
            
        # Check for spam patterns
        if self.threat_patterns['spam'].search(message):
            threats.append("Spam pattern detected")
            threat_level += 3
            
        # Check excessive caps
        if self.threat_patterns['caps'].search(message):
            threats.append("Excessive capitalization")
            threat_level += 2
            
        # Check for links (can be adjusted per group)
        if self.threat_patterns['links'].search(message):
            threats.append("Contains links")
            threat_level += 1
            
        # Check for personal info
        if self.threat_patterns['phone'].search(message):
            threats.append("Phone number detected")
            threat_level += 4
            
        if self.threat_patterns['email'].search(message):
            threats.append("Email address detected")
            threat_level += 3
            
        # Check rate limiting
        rate_key = f"{user_id}:{group_id}" if group_id else str(user_id)
        if not self._check_rate_limit(rate_key):
            threats.append("Rate limit exceeded")
            threat_level += 5
            
        # Determine action
        if threat_level >= 8:
            action = "ban"
        elif threat_level >= 5:
            action = "mute"
        elif threat_level >= 3:
            action = "warn"
        else:
            action = "monitor"
            
        # Update suspicious users
        if threat_level > 0:
            await self._update_suspicious_user(user_id, threat_level, threats)
            
        return ThreatDetection(
            is_threat=threat_level > 0,
            threat_level=threat_level,
            reasons=threats,
            action=action
        )
        
    def _check_rate_limit(self, key: str, limit: int = 10, window: int = 60) -> bool:
        """
        Check rate limit
        
        Args:
            key: Rate limit key
            limit: Max requests per window
            window: Time window in seconds
            
        Returns:
            True if within limits
        """
        current_time = asyncio.get_event_loop().time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {
                'count': 1,
                'window_start': current_time
            }
            return True
            
        rate_data = self.rate_limits[key]
        
        # Reset window if expired
        if current_time - rate_data['window_start'] > window:
            rate_data['count'] = 1
            rate_data['window_start'] = current_time
            return True
            
        # Check limit
        if rate_data['count'] >= limit:
            return False
            
        rate_data['count'] += 1
        return True
        
    async def _update_suspicious_user(self, user_id: int, threat_level: int, reasons: List[str]):
        """Update suspicious user tracking"""
        if user_id not in self.suspicious_users:
            self.suspicious_users[user_id] = {
                'threat_count': 0,
                'total_threat_level': 0,
                'first_seen': asyncio.get_event_loop().time(),
                'last_seen': asyncio.get_event_loop().time(),
                'reasons': set()
            }
            
        user_data = self.suspicious_users[user_id]
        user_data['threat_count'] += 1
        user_data['total_threat_level'] += threat_level
        user_data['last_seen'] = asyncio.get_event_loop().time()
        user_data['reasons'].update(reasons)
        
        # Auto-ban if too many threats
        avg_threat = user_data['total_threat_level'] / user_data['threat_count']
        if user_data['threat_count'] >= 5 and avg_threat >= 3:
            await self.ban_user(user_id, "Automatic ban: Repeated threats")
            
    async def create_alert(self, alert_type: str, message: str, 
                         severity: int = 5, user_id: Optional[int] = None,
                         group_id: Optional[int] = None, data: Dict = None):
        """
        Create security alert
        
        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Severity level 1-10
            user_id: Related user ID
            group_id: Related group ID
            data: Additional data
        """
        alert_id = hashlib.sha256(f"{alert_type}{message}{user_id}".encode()).hexdigest()[:16]
        
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            user_id=user_id,
            group_id=group_id,
            timestamp=asyncio.get_event_loop().time(),
            data=data or {}
        )
        
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
            
        self.logger.warning(f"🚨 Security Alert [{severity}/10]: {message}")
        
        # Log to file
        await self._log_alert(alert)
        
    async def _log_alert(self, alert: SecurityAlert):
        """Log alert to file"""
        try:
            log_file = "data/security_logs.json"
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'alert_id': alert.alert_id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'user_id': alert.user_id,
                'group_id': alert.group_id,
                'data': alert.data
            }
            
            import json
            from pathlib import Path
            
            Path("data").mkdir(exist_ok=True)
            
            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            self.logger.error(f"❌ Error logging alert: {e}")
            
    async def ban_user(self, user_id: int, reason: str = ""):
        """
        Ban a user
        
        Args:
            user_id: User ID to ban
            reason: Ban reason
        """
        self.blacklist.add(user_id)
        
        await self.create_alert(
            alert_type="user_banned",
            message=f"User {user_id} banned: {reason}",
            severity=8,
            user_id=user_id,
            data={'reason': reason}
        )
        
        self.logger.warning(f"⚡ User {user_id} banned: {reason}")
        
    async def unban_user(self, user_id: int):
        """Unban a user"""
        if user_id in self.blacklist:
            self.blacklist.remove(user_id)
            self.logger.info(f"✅ User {user_id} unbanned")
            
    def is_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        return user_id in self.blacklist
        
    async def scan_group(self, group_id: int) -> Dict[str, Any]:
        """
        Scan group for security issues
        
        Args:
            group_id: Group ID to scan
            
        Returns:
            Scan results
        """
        # TODO: Implement group scanning
        return {
            'group_id': group_id,
            'scan_time': datetime.now().isoformat(),
            'issues_found': 0,
            'recommendations': []
        }
        
    def get_alerts(self, limit: int = 50, min_severity: int = 0) -> List[SecurityAlert]:
        """Get recent alerts"""
        filtered = [a for a in self.alerts if a.severity >= min_severity]
        return filtered[-limit:] if limit else filtered
        
    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        current_time = asyncio.get_event_loop().time()
        recent_alerts = [a for a in self.alerts 
                        if current_time - a.timestamp < 3600]  # Last hour
        
        return {
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent_alerts),
            'banned_users': len(self.blacklist),
            'suspicious_users': len(self.suspicious_users),
            'alert_severity_distribution': self._get_severity_distribution()
        }
        
    def _get_severity_distribution(self) -> Dict[int, int]:
        """Get alert severity distribution"""
        distribution = {i: 0 for i in range(1, 11)}
        for alert in self.alerts:
            distribution[alert.severity] += 1
        return distribution
        
    async def cleanup_old_data(self, max_age_hours: int = 720):
        """Cleanup old security data"""
        current_time = asyncio.get_event_loop().time()
        max_age = max_age_hours * 3600
        
        # Clean old alerts
        self.alerts = [a for a in self.alerts 
                      if current_time - a.timestamp < max_age]
                      
        # Clean old suspicious users
        old_users = []
        for user_id, data in self.suspicious_users.items():
            if current_time - data['last_seen'] > max_age:
                old_users.append(user_id)
                
        for user_id in old_users:
            del self.suspicious_users[user_id]
            
        self.logger.info(f"🧹 Cleaned {len(old_users)} old suspicious users")