"""
Auto-Ban System - Automatically bans users based on rules
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

class BanReason(Enum):
    """Reasons for banning"""
    SPAM = "spam"
    FLOOD = "flood"
    BADWORD = "badword"
    LINKS = "malicious_links"
    SCAM = "scam"
    ADVERTISEMENT = "advertisement"
    HARASSMENT = "harassment"
    MANUAL = "manual"
    PERSISTENT_VIOLATIONS = "persistent_violations"

class AutoBan:
    """Automatic user banning system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_autoban")
        self.banned_users = {}
        self.ban_history = []
        self.ban_rules = {}
        self.temp_bans = {}
        
        # Default configuration
        self.config = {
            "enabled": True,
            "auto_ban_enabled": True,
            "ban_durations": {
                "spam": 86400,           # 1 day
                "flood": 172800,         # 2 days
                "badword": 259200,       # 3 days
                "malicious_links": 604800, # 7 days
                "scam": 2592000,         # 30 days
                "advertisement": 604800, # 7 days
                "harassment": 2592000,   # 30 days
                "manual": 0,             # Permanent
                "persistent_violations": 2592000  # 30 days
            },
            "escalation": {
                "second_offense_multiplier": 3,
                "third_offense_multiplier": 10,
                "persistent_multiplier": 30,
                "max_temp_duration": 2592000,  # 30 days
                "permanent_after": 3
            },
            "violation_points": {
                "spam": 5,
                "flood": 3,
                "badword": 10,
                "malicious_links": 15,
                "scam": 20,
                "advertisement": 8,
                "harassment": 15
            },
            "ban_threshold": 30,
            "notify_user": True,
            "notify_admins": True,
            "allow_appeal": True,
            "appeal_cooldown": 86400  # 24 hours
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default ban rules"""
        self.ban_rules = {
            "auto_ban_spam": {
                "enabled": True,
                "type": "points",
                "threshold": 30,
                "action": "temp_ban",
                "duration": "spam",
                "notify": True
            },
            "auto_ban_scam": {
                "enabled": True,
                "type": "instant",
                "action": "temp_ban",
                "duration": "scam",
                "notify": True
            },
            "auto_ban_malicious_links": {
                "enabled": True,
                "type": "instant",
                "action": "temp_ban",
                "duration": "malicious_links",
                "notify": True
            },
            "auto_ban_harassment": {
                "enabled": True,
                "type": "points",
                "threshold": 25,
                "action": "temp_ban",
                "duration": "harassment",
                "notify": True
            },
            "persistent_violator": {
                "enabled": True,
                "type": "violation_count",
                "threshold": 5,
                "time_window": 86400,
                "action": "temp_ban",
                "duration": "persistent_violations",
                "notify": True
            }
        }
        
    async def check_and_ban(self, user_id: int, violation_type: str,
                          group_id: Optional[int] = None,
                          details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Check if user should be banned and apply ban
        
        Args:
            user_id: User ID
            violation_type: Type of violation
            group_id: Group ID
            details: Additional details
            
        Returns:
            Ban information if banned, None otherwise
        """
        if not self.config["enabled"] or not self.config["auto_ban_enabled"]:
            return None
            
        user_key = self._get_user_key(user_id, group_id)
        
        # Check if user is already banned
        if self._is_user_banned(user_key):
            return self._get_ban_info(user_key)
            
        # Add violation points
        points = self.config["violation_points"].get(violation_type, 5)
        await self._add_violation_points(user_key, violation_type, points, details)
        
        # Check rules
        for rule_name, rule in self.ban_rules.items():
            if not rule["enabled"]:
                continue
                
            should_ban = await self._check_rule(user_key, rule, violation_type, details)
            
            if should_ban:
                # Calculate ban duration
                duration_type = rule.get("duration", violation_type)
                base_duration = self.config["ban_durations"].get(duration_type, 86400)
                
                offense_count = await self._get_offense_count(user_key, violation_type)
                duration = self._calculate_duration(base_duration, offense_count)
                
                # Apply ban
                ban_info = await self.ban_user(
                    user_id=user_id,
                    group_id=group_id,
                    duration=duration,
                    reason=BanReason(violation_type),
                    rule_applied=rule_name,
                    details=details
                )
                
                return ban_info
                
        return None
        
    def _get_user_key(self, user_id: int, group_id: Optional[int]) -> str:
        """Get unique key for user"""
        if group_id:
            return f"{user_id}_{group_id}"
        return str(user_id)
        
    async def _add_violation_points(self, user_key: str, violation_type: str,
                                  points: int, details: Dict[str, Any] = None):
        """Add violation points to user"""
        # Get current points
        current_points = await self._get_violation_points(user_key)
        new_points = current_points + points
        
        # Record violation
        violation_record = {
            "user_key": user_key,
            "type": violation_type,
            "points": points,
            "total_points": new_points,
            "timestamp": datetime.now(),
            "details": details or {}
        }
        
        self.ban_history.append(violation_record)
        
        # Check if points exceed threshold
        if new_points >= self.config["ban_threshold"]:
            # This will be handled by the points-based rule
            pass
            
    async def _get_violation_points(self, user_key: str) -> int:
        """Get total violation points for user"""
        points = 0
        
        for record in self.ban_history:
            if record["user_key"] == user_key:
                # Check if points have expired (24 hours)
                time_diff = (datetime.now() - record["timestamp"]).total_seconds()
                if time_diff <= 86400:  # 24 hours
                    points += record["points"]
                    
        return points
        
    async def _get_offense_count(self, user_key: str, violation_type: str) -> int:
        """Get offense count for specific violation type"""
        count = 0
        current_time = datetime.now()
        
        for record in self.ban_history:
            if (record["user_key"] == user_key and
                record["type"] == violation_type and
                (current_time - record["timestamp"]).total_seconds() <= 86400):  # 24 hours
                count += 1
                
        return count
        
    async def _check_rule(self, user_key: str, rule: Dict[str, Any],
                        violation_type: str, details: Dict[str, Any]) -> bool:
        """Check if rule applies"""
        rule_type = rule.get("type", "points")
        
        if rule_type == "instant":
            # Instant ban for specific violations
            trigger_violations = rule.get("trigger_violations", [])
            return violation_type in trigger_violations
            
        elif rule_type == "points":
            # Points-based ban
            threshold = rule.get("threshold", self.config["ban_threshold"])
            points = await self._get_violation_points(user_key)
            return points >= threshold
            
        elif rule_type == "violation_count":
            # Ban based on number of violations
            threshold = rule.get("threshold", 5)
            time_window = rule.get("time_window", 86400)
            
            count = 0
            current_time = datetime.now()
            
            for record in self.ban_history:
                if record["user_key"] == user_key:
                    time_diff = (current_time - record["timestamp"]).total_seconds()
                    if time_diff <= time_window:
                        count += 1
                        
            return count >= threshold
            
        return False
        
    def _calculate_duration(self, base_duration: int, offense_count: int) -> int:
        """Calculate ban duration based on offense count"""
        if offense_count == 0:
            return base_duration
        elif offense_count == 1:
            multiplier = self.config["escalation"]["second_offense_multiplier"]
        elif offense_count == 2:
            multiplier = self.config["escalation"]["third_offense_multiplier"]
        else:
            multiplier = self.config["escalation"]["persistent_multiplier"]
            
        duration = base_duration * multiplier
        max_duration = self.config["escalation"]["max_temp_duration"]
        
        # Check for permanent ban
        if offense_count >= self.config["escalation"]["permanent_after"]:
            return 0  # 0 means permanent
            
        return min(duration, max_duration)
        
    async def ban_user(self, user_id: int, duration: int,
                      reason: BanReason, group_id: Optional[int] = None,
                      banned_by: Optional[int] = None,
                      rule_applied: Optional[str] = None,
                      details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ban a user
        
        Args:
            user_id: User ID
            duration: Ban duration in seconds (0 for permanent)
            reason: Ban reason
            group_id: Group ID
            banned_by: User who banned
            rule_applied: Rule that triggered ban
            details: Additional details
            
        Returns:
            Ban information
        """
        user_key = self._get_user_key(user_id, group_id)
        
        if duration == 0:
            # Permanent ban
            ban_until = None
            ban_type = "permanent"
        else:
            # Temporary ban
            ban_until = datetime.now() + timedelta(seconds=duration)
            ban_type = "temporary"
            
        ban_info = {
            "user_id": user_id,
            "group_id": group_id,
            "banned_until": ban_until,
            "duration": duration,
            "ban_type": ban_type,
            "reason": reason.value,
            "banned_by": banned_by,
            "rule_applied": rule_applied,
            "banned_at": datetime.now(),
            "details": details or {},
            "user_key": user_key,
            "can_appeal": self.config["allow_appeal"] and ban_type == "temporary"
        }
        
        self.banned_users[user_key] = ban_info
        
        # Add to history
        self.ban_history.append({
            **ban_info,
            "timestamp": datetime.now(),
            "action": "ban"
        })
        
        # Notify if configured
        if self.config["notify_user"]:
            await self._notify_user(user_id, ban_info)
            
        if self.config["notify_admins"]:
            await self._notify_admins(user_id, ban_info)
            
        if ban_type == "permanent":
            self.logger.warning(f"🔨 Permanently banned user {user_key}: {reason.value}")
        else:
            self.logger.warning(f"🔨 Banned user {user_key} for {duration}s: {reason.value}")
            
        return ban_info
        
    async def unban_user(self, user_id: int,
                        group_id: Optional[int] = None) -> bool:
        """
        Unban a user
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if unbanned
        """
        user_key = self._get_user_key(user_id, group_id)
        
        if user_key in self.banned_users:
            ban_info = self.banned_users[user_key]
            
            # Add to history
            self.ban_history.append({
                "user_key": user_key,
                "user_id": user_id,
                "group_id": group_id,
                "action": "unban",
                "timestamp": datetime.now(),
                "original_ban": ban_info
            })
            
            del self.banned_users[user_key]
            
            self.logger.info(f"✅ Unbanned user {user_key}")
            return True
            
        return False
        
    def _is_user_banned(self, user_key: str) -> bool:
        """Check if user is banned"""
        if user_key in self.banned_users:
            ban_info = self.banned_users[user_key]
            
            if ban_info["ban_type"] == "permanent":
                return True
            else:
                # Check if temporary ban has expired
                if datetime.now() < ban_info["banned_until"]:
                    return True
                else:
                    # Ban expired, remove
                    del self.banned_users[user_key]
                    return False
        return False
        
    def _get_ban_info(self, user_key: str) -> Optional[Dict[str, Any]]:
        """Get ban information for user"""
        if user_key in self.banned_users:
            ban_info = self.banned_users[user_key].copy()
            
            if ban_info["ban_type"] == "temporary":
                # Calculate remaining time
                remaining = (ban_info["banned_until"] - datetime.now()).total_seconds()
                ban_info["remaining_seconds"] = max(0, int(remaining))
                
            return ban_info
        return None
        
    async def _notify_user(self, user_id: int, ban_info: Dict[str, Any]):
        """Notify user about ban"""
        # This would send a message to the user
        reason = ban_info["reason"]
        duration = ban_info["duration"]
        
        if ban_info["ban_type"] == "permanent":
            message = f"Permanently banned for: {reason}"
        else:
            message = f"Banned for {duration} seconds: {reason}"
            
        self.logger.info(f"📨 Would notify user {user_id}: {message}")
        
    async def _notify_admins(self, user_id: int, ban_info: Dict[str, Any]):
        """Notify admins about ban"""
        # This would notify group admins
        self.logger.info(f"📨 Would notify admins about user {user_id} ban")
        
    async def get_user_ban_status(self, user_id: int,
                                group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user's ban status"""
        user_key = self._get_user_key(user_id, group_id)
        
        if self._is_user_banned(user_key):
            ban_info = self._get_ban_info(user_key)
            return {
                "is_banned": True,
                **ban_info
            }
        else:
            return {
                "is_banned": False,
                "user_id": user_id,
                "group_id": group_id
            }
            
    async def get_user_ban_history(self, user_id: int,
                                 group_id: Optional[int] = None,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's ban history"""
        user_key = self._get_user_key(user_id, group_id)
        
        user_history = []
        for record in self.ban_history:
            if record.get("user_key") == user_key:
                user_history.append(record)
                
        # Sort by timestamp (newest first)
        user_history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        return user_history[:limit]
        
    async def cleanup_expired_bans(self):
        """Cleanup expired bans"""
        current_time = datetime.now()
        expired_keys = []
        
        for user_key, ban_info in self.banned_users.items():
            if (ban_info["ban_type"] == "temporary" and
                current_time >= ban_info["banned_until"]):
                expired_keys.append(user_key)
                
        for key in expired_keys:
            del self.banned_users[key]
            
        if expired_keys:
            self.logger.info(f"🧹 Cleaned up {len(expired_keys)} expired bans")
            
    async def get_user_violation_stats(self, user_id: int,
                                     group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user's violation statistics"""
        user_key = self._get_user_key(user_id, group_id)
        
        total_points = await self._get_violation_points(user_key)
        
        # Count violations by type (last 24 hours)
        violation_counts = {}
        current_time = datetime.now()
        
        for record in self.ban_history:
            if record["user_key"] == user_key:
                time_diff = (current_time - record["timestamp"]).total_seconds()
                if time_diff <= 86400:  # 24 hours
                    vtype = record["type"]
                    violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
                    
        return {
            "user_id": user_id,
            "group_id": group_id,
            "total_violation_points": total_points,
            "violation_counts": violation_counts,
            "is_close_to_ban": total_points >= (self.config["ban_threshold"] * 0.7)
        }
        
    async def appeal_ban(self, user_id: int, group_id: Optional[int] = None,
                       appeal_message: str = "") -> Dict[str, Any]:
        """
        Submit ban appeal
        
        Args:
            user_id: User ID
            group_id: Group ID
            appeal_message: Appeal message
            
        Returns:
            Appeal result
        """
        user_key = self._get_user_key(user_id, group_id)
        
        if not self.config["allow_appeal"]:
            return {
                "success": False,
                "message": "Appeals are not allowed"
            }
            
        if not self._is_user_banned(user_key):
            return {
                "success": False,
                "message": "User is not banned"
            }
            
        ban_info = self._get_ban_info(user_key)
        
        if ban_info["ban_type"] == "permanent":
            return {
                "success": False,
                "message": "Permanent bans cannot be appealed"
            }
            
        # Check cooldown
        last_appeal = await self._get_last_appeal(user_key)
        if last_appeal:
            time_since = (datetime.now() - last_appeal).total_seconds()
            if time_since < self.config["appeal_cooldown"]:
                remaining = self.config["appeal_cooldown"] - time_since
                return {
                    "success": False,
                    "message": f"Please wait {int(remaining/3600)} hours before appealing again"
                }
                
        # Record appeal
        appeal_record = {
            "user_key": user_key,
            "user_id": user_id,
            "group_id": group_id,
            "appeal_message": appeal_message,
            "timestamp": datetime.now(),
            "ban_info": ban_info
        }
        
        self.ban_history.append(appeal_record)
        
        # Notify admins
        await self._notify_admins_appeal(user_id, appeal_record)
        
        return {
            "success": True,
            "message": "Appeal submitted successfully",
            "appeal_id": len(self.ban_history),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_last_appeal(self, user_key: str) -> Optional[datetime]:
        """Get last appeal timestamp for user"""
        last_appeal = None
        
        for record in reversed(self.ban_history):
            if record.get("user_key") == user_key and "appeal_message" in record:
                last_appeal = record["timestamp"]
                break
                
        return last_appeal
        
    async def _notify_admins_appeal(self, user_id: int, appeal_record: Dict[str, Any]):
        """Notify admins about ban appeal"""
        self.logger.info(f"📨 Would notify admins about ban appeal from user {user_id}")
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get auto-ban system statistics"""
        currently_banned = sum(1 for ban_info in self.banned_users.values()
                             if self._is_user_banned(ban_info["user_key"]))
        
        permanent_bans = sum(1 for ban_info in self.banned_users.values()
                           if ban_info["ban_type"] == "permanent")
        
        # Count bans by reason
        reason_counts = {}
        for record in self.ban_history:
            if record.get("action") == "ban":
                reason = record.get("reason", "unknown")
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
        return {
            "currently_banned_users": currently_banned,
            "permanent_bans": permanent_bans,
            "temporary_bans": currently_banned - permanent_bans,
            "total_ban_records": len(self.ban_history),
            "ban_rules_count": len(self.ban_rules),
            "bans_by_reason": reason_counts,
            "config": self.config
        }