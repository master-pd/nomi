"""
Auto-Mute System - Automatically mutes users based on rules
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

class MuteReason(Enum):
    """Reasons for muting"""
    SPAM = "spam"
    FLOOD = "flood"
    BADWORD = "badword"
    LINKS = "links"
    CAPS = "excessive_caps"
    REPETITION = "repetition"
    ADVERTISEMENT = "advertisement"
    MANUAL = "manual"

class AutoMute:
    """Automatic user muting system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_automute")
        self.muted_users = {}
        self.mute_history = []
        self.mute_rules = {}
        
        # Default configuration
        self.config = {
            "enabled": True,
            "auto_mute_enabled": True,
            "mute_durations": {
                "spam": 300,           # 5 minutes
                "flood": 600,          # 10 minutes
                "badword": 900,        # 15 minutes
                "links": 300,          # 5 minutes
                "caps": 180,           # 3 minutes
                "repetition": 240,     # 4 minutes
                "advertisement": 1200, # 20 minutes
                "manual": 3600         # 1 hour
            },
            "escalation": {
                "second_offense_multiplier": 2,
                "third_offense_multiplier": 4,
                "persistent_multiplier": 10,
                "max_duration": 604800  # 7 days
            },
            "notify_user": True,
            "notify_admins": False,
            "auto_unmute": True
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default mute rules"""
        self.mute_rules = {
            "spam": {
                "enabled": True,
                "threshold": 5,
                "time_window": 60,
                "action": "auto_mute",
                "duration": "spam",
                "notify": True
            },
            "flood": {
                "enabled": True,
                "threshold": 15,
                "time_window": 60,
                "action": "auto_mute",
                "duration": "flood",
                "notify": True
            },
            "badword": {
                "enabled": True,
                "threshold": 3,
                "time_window": 3600,
                "action": "auto_mute",
                "duration": "badword",
                "notify": True
            },
            "links": {
                "enabled": True,
                "threshold": 5,
                "time_window": 300,
                "action": "auto_mute",
                "duration": "links",
                "notify": True
            },
            "caps": {
                "enabled": True,
                "threshold": 10,
                "time_window": 300,
                "action": "auto_mute",
                "duration": "caps",
                "notify": True
            }
        }
        
    async def check_and_mute(self, user_id: int, violation_type: str,
                           group_id: Optional[int] = None,
                           details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Check if user should be muted and apply mute
        
        Args:
            user_id: User ID
            violation_type: Type of violation
            group_id: Group ID
            details: Additional details
            
        Returns:
            Mute information if muted, None otherwise
        """
        if not self.config["enabled"] or not self.config["auto_mute_enabled"]:
            return None
            
        # Check if rule is enabled
        rule = self.mute_rules.get(violation_type)
        if not rule or not rule["enabled"]:
            return None
            
        user_key = self._get_user_key(user_id, group_id)
        
        # Check if user is already muted
        if self._is_user_muted(user_key):
            return self._get_mute_info(user_key)
            
        # Check violation count
        violation_count = await self._get_violation_count(user_key, violation_type,
                                                        rule["time_window"])
        
        if violation_count >= rule["threshold"]:
            # Calculate mute duration
            base_duration = self.config["mute_durations"].get(rule["duration"], 300)
            offense_count = await self._get_offense_count(user_key, violation_type)
            
            duration = self._calculate_duration(base_duration, offense_count)
            
            # Apply mute
            mute_info = await self.mute_user(
                user_id=user_id,
                group_id=group_id,
                duration=duration,
                reason=MuteReason(violation_type),
                details=details
            )
            
            # Record violation
            await self._record_violation(user_key, violation_type, details)
            
            return mute_info
            
        return None
        
    def _get_user_key(self, user_id: int, group_id: Optional[int]) -> str:
        """Get unique key for user"""
        if group_id:
            return f"{user_id}_{group_id}"
        return str(user_id)
        
    async def _get_violation_count(self, user_key: str, violation_type: str,
                                 time_window: int) -> int:
        """Get violation count for user within time window"""
        count = 0
        current_time = datetime.now()
        
        # Check mute history
        for record in self.mute_history:
            if (record["user_key"] == user_key and
                record["reason"] == violation_type and
                (current_time - record["timestamp"]).total_seconds() <= time_window):
                count += 1
                
        return count
        
    async def _get_offense_count(self, user_key: str, violation_type: str) -> int:
        """Get total offense count for user"""
        count = 0
        
        for record in self.mute_history:
            if record["user_key"] == user_key and record["reason"] == violation_type:
                count += 1
                
        return count
        
    def _calculate_duration(self, base_duration: int, offense_count: int) -> int:
        """Calculate mute duration based on offense count"""
        if offense_count == 0:
            return base_duration
        elif offense_count == 1:
            multiplier = self.config["escalation"]["second_offense_multiplier"]
        elif offense_count == 2:
            multiplier = self.config["escalation"]["third_offense_multiplier"]
        else:
            multiplier = self.config["escalation"]["persistent_multiplier"]
            
        duration = base_duration * multiplier
        max_duration = self.config["escalation"]["max_duration"]
        
        return min(duration, max_duration)
        
    async def _record_violation(self, user_key: str, violation_type: str,
                              details: Dict[str, Any] = None):
        """Record violation in history"""
        record = {
            "user_key": user_key,
            "reason": violation_type,
            "timestamp": datetime.now(),
            "details": details or {}
        }
        
        self.mute_history.append(record)
        
        # Keep only last 1000 records
        if len(self.mute_history) > 1000:
            self.mute_history = self.mute_history[-1000:]
            
    async def mute_user(self, user_id: int, duration: int,
                       reason: MuteReason, group_id: Optional[int] = None,
                       muted_by: Optional[int] = None,
                       details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mute a user
        
        Args:
            user_id: User ID
            duration: Mute duration in seconds
            reason: Mute reason
            group_id: Group ID
            muted_by: User who muted
            details: Additional details
            
        Returns:
            Mute information
        """
        user_key = self._get_user_key(user_id, group_id)
        
        mute_until = datetime.now() + timedelta(seconds=duration)
        
        mute_info = {
            "user_id": user_id,
            "group_id": group_id,
            "muted_until": mute_until,
            "duration": duration,
            "reason": reason.value,
            "muted_by": muted_by,
            "muted_at": datetime.now(),
            "details": details or {},
            "user_key": user_key
        }
        
        self.muted_users[user_key] = mute_info
        
        # Add to history
        self.mute_history.append({
            **mute_info,
            "timestamp": datetime.now(),
            "action": "mute"
        })
        
        # Notify if configured
        if self.config["notify_user"]:
            await self._notify_user(user_id, mute_info)
            
        if self.config["notify_admins"]:
            await self._notify_admins(user_id, mute_info)
            
        self.logger.warning(f"🔇 Muted user {user_key} for {duration}s: {reason.value}")
        
        return mute_info
        
    async def unmute_user(self, user_id: int,
                         group_id: Optional[int] = None) -> bool:
        """
        Unmute a user
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if unmuted
        """
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key in self.muted_users:
            mute_info = self.muted_users[user_key]
            
            # Add to history
            self.mute_history.append({
                "user_key": user_key,
                "user_id": user_id,
                "group_id": group_id,
                "action": "unmute",
                "timestamp": datetime.now(),
                "original_mute": mute_info
            })
            
            del self.muted_users[user_key]
            
            self.logger.info(f"🔊 Unmuted user {user_key}")
            return True
            
        return False
        
    def _is_user_muted(self, user_key: str) -> bool:
        """Check if user is muted"""
        if user_key in self.muted_users:
            mute_info = self.muted_users[user_key]
            if datetime.now() < mute_info["muted_until"]:
                return True
            else:
                # Mute expired, remove
                del self.muted_users[user_key]
                return False
        return False
        
    def _get_mute_info(self, user_key: str) -> Optional[Dict[str, Any]]:
        """Get mute information for user"""
        if user_key in self.muted_users:
            mute_info = self.muted_users[user_key].copy()
            
            # Calculate remaining time
            remaining = (mute_info["muted_until"] - datetime.now()).total_seconds()
            mute_info["remaining_seconds"] = max(0, int(remaining))
            
            return mute_info
        return None
        
    async def _notify_user(self, user_id: int, mute_info: Dict[str, Any]):
        """Notify user about mute"""
        # This would send a message to the user
        # For now, just log
        duration = mute_info["duration"]
        reason = mute_info["reason"]
        
        self.logger.info(f"📨 Would notify user {user_id} about {duration}s mute for {reason}")
        
    async def _notify_admins(self, user_id: int, mute_info: Dict[str, Any]):
        """Notify admins about mute"""
        # This would notify group admins
        self.logger.info(f"📨 Would notify admins about user {user_id} mute")
        
    async def get_user_mute_status(self, user_id: int,
                                 group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user's mute status"""
        user_key = self._get_user_key(user_id, group_id)
        
        if self._is_user_muted(user_key):
            mute_info = self._get_mute_info(user_key)
            return {
                "is_muted": True,
                **mute_info
            }
        else:
            return {
                "is_muted": False,
                "user_id": user_id,
                "group_id": group_id
            }
            
    async def get_user_mute_history(self, user_id: int,
                                  group_id: Optional[int] = None,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's mute history"""
        user_key = self._get_user_key(user_id, group_id)
        
        user_history = []
        for record in self.mute_history:
            if record.get("user_key") == user_key:
                user_history.append(record)
                
        # Sort by timestamp (newest first)
        user_history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        return user_history[:limit]
        
    async def cleanup_expired_mutes(self):
        """Cleanup expired mutes"""
        current_time = datetime.now()
        expired_keys = []
        
        for user_key, mute_info in self.muted_users.items():
            if current_time >= mute_info["muted_until"]:
                expired_keys.append(user_key)
                
        for key in expired_keys:
            del self.muted_users[key]
            
        if expired_keys:
            self.logger.info(f"🧹 Cleaned up {len(expired_keys)} expired mutes")
            
    async def update_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update mute rule
        
        Args:
            rule_name: Rule name
            updates: Rule updates
            
        Returns:
            True if updated
        """
        if rule_name not in self.mute_rules:
            return False
            
        self.mute_rules[rule_name].update(updates)
        self.logger.info(f"⚙️ Updated rule: {rule_name}")
        return True
        
    async def add_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> bool:
        """
        Add new mute rule
        
        Args:
            rule_name: Rule name
            rule_config: Rule configuration
            
        Returns:
            True if added
        """
        if rule_name in self.mute_rules:
            return False
            
        self.mute_rules[rule_name] = rule_config
        self.logger.info(f"➕ Added new rule: {rule_name}")
        return True
        
    async def remove_rule(self, rule_name: str) -> bool:
        """
        Remove mute rule
        
        Args:
            rule_name: Rule name
            
        Returns:
            True if removed
        """
        if rule_name in self.mute_rules:
            del self.mute_rules[rule_name]
            self.logger.info(f"🗑️ Removed rule: {rule_name}")
            return True
        return False
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get auto-mute system statistics"""
        currently_muted = sum(1 for mute_info in self.muted_users.values()
                            if datetime.now() < mute_info["muted_until"])
        
        # Count mutes by reason
        reason_counts = {}
        for record in self.mute_history:
            if record.get("action") == "mute":
                reason = record.get("reason", "unknown")
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
        return {
            "currently_muted_users": currently_muted,
            "total_mute_records": len(self.mute_history),
            "mute_rules_count": len(self.mute_rules),
            "mutes_by_reason": reason_counts,
            "config": self.config
        }
        
    async def export_rules(self) -> Dict[str, Any]:
        """Export mute rules"""
        return {
            "rules": self.mute_rules,
            "config": self.config,
            "export_time": datetime.now().isoformat()
        }
        
    async def import_rules(self, data: Dict[str, Any]) -> bool:
        """
        Import mute rules
        
        Args:
            data: Rules to import
            
        Returns:
            True if successful
        """
        try:
            if "rules" in data:
                self.mute_rules.update(data["rules"])
                
            if "config" in data:
                self.config.update(data["config"])
                
            self.logger.info("📥 Imported mute rules")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error importing rules: {e}")
            return False