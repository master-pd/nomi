"""
Warning System - Manages user warnings
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class WarningLevel(Enum):
    """Warning levels"""
    INFO = "info"
    WARNING = "warning"
    SEVERE = "severe"
    CRITICAL = "critical"

@dataclass
class Warning:
    """Warning data"""
    warning_id: str
    user_id: int
    group_id: Optional[int]
    level: WarningLevel
    reason: str
    issued_by: Optional[int]
    issued_at: datetime
    expires_at: Optional[datetime]
    points: int
    details: Dict[str, Any]

class WarningSystem:
    """User warning management system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_warnings")
        self.active_warnings = {}
        .warning_history = []
        self.warning_rules = {}
        
        # Default configuration
        self.config = {
            "enabled": True,
            "auto_warn_enabled": True,
            "warning_points": {
                "spam": 5,
                "flood": 3,
                "badword": 10,
                "links": 8,
                "caps": 2,
                "advertisement": 15,
                "harassment": 20,
                "scam": 25
            },
            "warning_levels": {
                "info": {"points": 1, "color": "blue"},
                "warning": {"points": 5, "color": "yellow"},
                "severe": {"points": 10, "color": "orange"},
                "critical": {"points": 20, "color": "red"}
            },
            "actions": {
                "mute_after_points": 30,
                "mute_duration": 300,
                "ban_after_points": 50,
                "ban_duration": 86400,
                "auto_remove_after": 604800  # 7 days
            },
            "notify_user": True,
            "notify_admins": False
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default warning rules"""
        self.warning_rules = {
            "auto_warn_spam": {
                "enabled": True,
                "type": "points",
                "points": 5,
                "level": "warning",
                "reason": "Spam detected",
                "auto_issue": True
            },
            "auto_warn_badword": {
                "enabled": True,
                "type": "instant",
                "points": 10,
                "level": "severe",
                "reason": "Inappropriate language",
                "auto_issue": True
            },
            "auto_warn_links": {
                "enabled": True,
                "type": "points",
                "points": 8,
                "level": "warning",
                "reason": "Unauthorized links",
                "auto_issue": True
            },
            "auto_warn_harassment": {
                "enabled": True,
                "type": "instant",
                "points": 20,
                "level": "critical",
                "reason": "Harassment",
                "auto_issue": True
            }
        }
        
    async def issue_warning(self, user_id: int, reason: str,
                          level: WarningLevel = WarningLevel.WARNING,
                          points: Optional[int] = None,
                          group_id: Optional[int] = None,
                          issued_by: Optional[int] = None,
                          duration: Optional[int] = None,
                          details: Dict[str, Any] = None) -> Warning:
        """
        Issue a warning to user
        
        Args:
            user_id: User ID
            reason: Warning reason
            level: Warning level
            points: Warning points (None for default based on level)
            group_id: Group ID
            issued_by: User who issued warning
            duration: Warning duration in seconds (None for permanent)
            details: Additional details
            
        Returns:
            Warning object
        """
        # Generate warning ID
        warning_id = f"WRN_{user_id}_{int(datetime.now().timestamp())}"
        
        # Determine points
        if points is None:
            points = self.config["warning_levels"][level.value]["points"]
            
        # Calculate expiration
        expires_at = None
        if duration:
            expires_at = datetime.now() + timedelta(seconds=duration)
            
        # Create warning
        warning = Warning(
            warning_id=warning_id,
            user_id=user_id,
            group_id=group_id,
            level=level,
            reason=reason,
            issued_by=issued_by,
            issued_at=datetime.now(),
            expires_at=expires_at,
            points=points,
            details=details or {}
        )
        
        # Store warning
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key not in self.active_warnings:
            self.active_warnings[user_key] = []
            
        self.active_warnings[user_key].append(warning)
        
        # Add to history
        self.warning_history.append({
            **warning.__dict__,
            "action": "issued"
        })
        
        # Check total points
        total_points = await self.get_user_points(user_id, group_id)
        
        # Check if actions needed
        await self._check_actions(user_id, group_id, total_points)
        
        # Notify if configured
        if self.config["notify_user"]:
            await self._notify_user(warning)
            
        if self.config["notify_admins"]:
            await self._notify_admins(warning)
            
        self.logger.warning(f"⚠️ Issued warning to user {user_key}: {reason} ({points} points)")
        
        return warning
        
    async def auto_warn(self, user_id: int, violation_type: str,
                       group_id: Optional[int] = None,
                       details: Dict[str, Any] = None) -> Optional[Warning]:
        """
        Automatically issue warning based on violation
        
        Args:
            user_id: User ID
            violation_type: Type of violation
            group_id: Group ID
            details: Violation details
            
        Returns:
            Warning if issued, None otherwise
        """
        if not self.config["auto_warn_enabled"]:
            return None
            
        # Check if rule exists for this violation
        rule_key = f"auto_warn_{violation_type}"
        rule = self.warning_rules.get(rule_key)
        
        if not rule or not rule["enabled"]:
            return None
            
        # Issue warning
        warning = await self.issue_warning(
            user_id=user_id,
            reason=rule["reason"],
            level=WarningLevel(rule["level"]),
            points=rule["points"],
            group_id=group_id,
            issued_by=None,  # Auto-issued
            details=details
        )
        
        return warning
        
    def _get_user_key(self, user_id: int, group_id: Optional[int]) -> str:
        """Get unique key for user"""
        if group_id:
            return f"{user_id}_{group_id}"
        return str(user_id)
        
    async def get_user_points(self, user_id: int,
                            group_id: Optional[int] = None) -> int:
        """Get total warning points for user"""
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key not in self.active_warnings:
            return 0
            
        total_points = 0
        current_time = datetime.now()
        
        for warning in self.active_warnings[user_key]:
            # Check if warning is expired
            if warning.expires_at and current_time > warning.expires_at:
                continue
            total_points += warning.points
            
        return total_points
        
    async def _check_actions(self, user_id: int, group_id: Optional[int],
                           total_points: int):
        """Check if actions needed based on points"""
        mute_threshold = self.config["actions"]["mute_after_points"]
        ban_threshold = self.config["actions"]["ban_after_points"]
        
        user_key = self._get_user_key(user_id, group_id)
        
        if total_points >= ban_threshold:
            # Auto-ban
            ban_duration = self.config["actions"]["ban_duration"]
            await self._trigger_auto_ban(user_key, total_points, ban_duration)
            
        elif total_points >= mute_threshold:
            # Auto-mute
            mute_duration = self.config["actions"]["mute_duration"]
            await self._trigger_auto_mute(user_key, total_points, mute_duration)
            
    async def _trigger_auto_mute(self, user_key: str, points: int, duration: int):
        """Trigger auto-mute"""
        # This would integrate with the auto_mute system
        self.logger.warning(f"🔇 Auto-mute triggered for {user_key} ({points} points)")
        
    async def _trigger_auto_ban(self, user_key: str, points: int, duration: int):
        """Trigger auto-ban"""
        # This would integrate with the auto_ban system
        self.logger.warning(f"🔨 Auto-ban triggered for {user_key} ({points} points)")
        
    async def _notify_user(self, warning: Warning):
        """Notify user about warning"""
        # This would send a message to the user
        message = f"You have received a {warning.level.value} warning: {warning.reason}"
        self.logger.info(f"📨 Would notify user {warning.user_id}: {message}")
        
    async def _notify_admins(self, warning: Warning):
        """Notify admins about warning"""
        # This would notify group admins
        self.logger.info(f"📨 Would notify admins about warning for user {warning.user_id}")
        
    async def remove_warning(self, warning_id: str,
                           removed_by: Optional[int] = None,
                           reason: str = "") -> bool:
        """
        Remove a warning
        
        Args:
            warning_id: Warning ID to remove
            removed_by: User who removed warning
            reason: Removal reason
            
        Returns:
            True if removed
        """
        warning_found = None
        user_key = None
        
        # Find warning in active warnings
        for key, warnings in self.active_warnings.items():
            for warning in warnings:
                if warning.warning_id == warning_id:
                    warning_found = warning
                    user_key = key
                    break
            if warning_found:
                break
                
        if not warning_found:
            return False
            
        # Remove from active warnings
        self.active_warnings[user_key].remove(warning_found)
        
        # Add to history
        self.warning_history.append({
            "action": "removed",
            "warning_id": warning_id,
            "removed_by": removed_by,
            "reason": reason,
            "timestamp": datetime.now(),
            "original_warning": warning_found.__dict__
        })
        
        self.logger.info(f"🗑️ Removed warning {warning_id}: {reason}")
        return True
        
    async def expire_warnings(self):
        """Remove expired warnings"""
        current_time = datetime.now()
        expired_count = 0
        
        for user_key, warnings in list(self.active_warnings.items()):
            active_warnings = []
            
            for warning in warnings:
                if warning.expires_at and current_time > warning.expires_at:
                    # Warning expired
                    expired_count += 1
                    
                    # Add to history
                    self.warning_history.append({
                        "action": "expired",
                        "warning_id": warning.warning_id,
                        "timestamp": current_time,
                        "original_warning": warning.__dict__
                    })
                else:
                    active_warnings.append(warning)
                    
            if active_warnings:
                self.active_warnings[user_key] = active_warnings
            else:
                del self.active_warnings[user_key]
                
        if expired_count > 0:
            self.logger.info(f"🧹 Removed {expired_count} expired warnings")
            
    async def get_user_warnings(self, user_id: int,
                              group_id: Optional[int] = None,
                              active_only: bool = True) -> List[Warning]:
        """Get warnings for user"""
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key not in self.active_warnings:
            return []
            
        if active_only:
            current_time = datetime.now()
            active_warnings = []
            
            for warning in self.active_warnings[user_key]:
                if warning.expires_at and current_time > warning.expires_at:
                    continue
                active_warnings.append(warning)
                
            return active_warnings
        else:
            return self.active_warnings[user_key]
            
    async def get_user_warning_history(self, user_id: int,
                                     group_id: Optional[int] = None,
                                     limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's warning history"""
        user_key = self._get_user_key(user_id, group_id)
        
        history = []
        
        for record in self.warning_history:
            if (record.get("original_warning", {}).get("user_key") == user_key or
                record.get("original_warning", {}).get("user_id") == user_id):
                history.append(record)
                
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        return history[:limit]
        
    async def clear_user_warnings(self, user_id: int,
                                group_id: Optional[int] = None,
                                cleared_by: Optional[int] = None,
                                reason: str = "") -> int:
        """
        Clear all warnings for user
        
        Args:
            user_id: User ID
            group_id: Group ID
            cleared_by: User who cleared warnings
            reason: Clear reason
            
        Returns:
            Number of warnings cleared
        """
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key not in self.active_warnings:
            return 0
            
        warnings_cleared = len(self.active_warnings[user_key])
        
        # Add to history
        for warning in self.active_warnings[user_key]:
            self.warning_history.append({
                "action": "cleared",
                "warning_id": warning.warning_id,
                "cleared_by": cleared_by,
                "reason": reason,
                "timestamp": datetime.now(),
                "original_warning": warning.__dict__
            })
            
        # Clear warnings
        del self.active_warnings[user_key]
        
        self.logger.info(f"🧹 Cleared {warnings_cleared} warnings for user {user_key}")
        return warnings_cleared
        
    async def get_warning_stats(self, user_id: int,
                              group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get warning statistics for user"""
        active_warnings = await self.get_user_warnings(user_id, group_id, active_only=True)
        all_warnings = await self.get_user_warnings(user_id, group_id, active_only=False)
        
        total_points = await self.get_user_points(user_id, group_id)
        
        # Count by level
        level_counts = {}
        for warning in all_warnings:
            level = warning.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
            
        return {
            "user_id": user_id,
            "group_id": group_id,
            "active_warnings": len(active_warnings),
            "total_warnings": len(all_warnings),
            "total_points": total_points,
            "warnings_by_level": level_counts,
            "mute_threshold": self.config["actions"]["mute_after_points"],
            "ban_threshold": self.config["actions"]["ban_after_points"],
            "close_to_mute": total_points >= (self.config["actions"]["mute_after_points"] * 0.7),
            "close_to_ban": total_points >= (self.config["actions"]["ban_after_points"] * 0.7)
        }
        
    async def update_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update warning rule
        
        Args:
            rule_name: Rule name
            updates: Rule updates
            
        Returns:
            True if updated
        """
        if rule_name not in self.warning_rules:
            return False
            
        self.warning_rules[rule_name].update(updates)
        self.logger.info(f"⚙️ Updated warning rule: {rule_name}")
        return True
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get warning system statistics"""
        total_active_warnings = sum(len(warnings) for warnings in self.active_warnings.values())
        
        # Count warnings by level
        level_counts = {}
        for warnings in self.active_warnings.values():
            for warning in warnings:
                level = warning.level.value
                level_counts[level] = level_counts.get(level, 0) + 1
                
        return {
            "users_with_warnings": len(self.active_warnings),
            "total_active_warnings": total_active_warnings,
            "total_warning_history": len(self.warning_history),
            "warnings_by_level": level_counts,
            "warning_rules_count": len(self.warning_rules),
            "config": self.config
        }
        
    async def export_warnings(self) -> Dict[str, Any]:
        """Export warning data"""
        return {
            "active_warnings": {
                key: [w.__dict__ for w in warnings]
                for key, warnings in self.active_warnings.items()
            },
            "warning_history": self.warning_history[-1000:],  # Last 1000 records
            "config": self.config,
            "rules": self.warning_rules,
            "export_time": datetime.now().isoformat()
        }