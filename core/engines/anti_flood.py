"""
Anti-Flood System - Prevents message flooding
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class AntiFlood:
    """Anti-flood protection system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_antiflood")
        self.user_message_count = defaultdict(int)
        self.user_first_message_time = {}
        self.user_warnings = defaultdict(int)
        self.muted_users = {}
        self.group_settings = {}
        
        # Default configuration
        self.config = {
            "max_messages_per_second": 2,
            "max_messages_per_minute": 15,
            "max_messages_per_5minutes": 50,
            "warning_threshold": 3,
            "mute_duration": {
                "first_offense": 60,      # 1 minute
                "second_offense": 300,    # 5 minutes
                "third_offense": 1800,    # 30 minutes
                "persistent": 86400       # 24 hours
            },
            "auto_reset_time": 300,       # 5 minutes
            "enabled": True
        }
        
    async def check_flood(self, user_id: int, group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if user is flooding
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            Flood check result
        """
        if not self.config["enabled"]:
            return {"is_flooding": False, "action": "allow"}
            
        current_time = datetime.now()
        user_key = self._get_user_key(user_id, group_id)
        
        # Check if user is muted
        if self._is_user_muted(user_key):
            return {
                "is_flooding": True,
                "reason": "user_muted",
                "action": "block",
                "mute_remaining": self._get_mute_remaining(user_key)
            }
            
        # Update message count
        self._update_message_count(user_key, current_time)
        
        # Check flood conditions
        flood_result = await self._analyze_flood_pattern(user_key, current_time)
        
        if flood_result["is_flooding"]:
            # Increment warnings
            self.user_warnings[user_key] += 1
            warnings = self.user_warnings[user_key]
            
            # Determine mute duration based on warnings
            if warnings >= 4:
                mute_duration = self.config["mute_duration"]["persistent"]
            elif warnings == 3:
                mute_duration = self.config["mute_duration"]["third_offense"]
            elif warnings == 2:
                mute_duration = self.config["mute_duration"]["second_offense"]
            else:
                mute_duration = self.config["mute_duration"]["first_offense"]
                
            # Mute user
            self._mute_user(user_key, mute_duration, flood_result["reason"])
            
            flood_result.update({
                "warnings": warnings,
                "mute_duration": mute_duration,
                "muted_until": (current_time + timedelta(seconds=mute_duration)).isoformat()
            })
            
        # Reset if user has been inactive
        self._check_inactivity(user_key, current_time)
        
        return flood_result
        
    def _get_user_key(self, user_id: int, group_id: Optional[int]) -> str:
        """Get unique key for user (with group context)"""
        if group_id:
            return f"{user_id}_{group_id}"
        return str(user_id)
        
    def _update_message_count(self, user_key: str, current_time: datetime):
        """Update message count for user"""
        if user_key not in self.user_first_message_time:
            self.user_first_message_time[user_key] = current_time
            self.user_message_count[user_key] = 0
            
        self.user_message_count[user_key] += 1
        
    async def _analyze_flood_pattern(self, user_key: str, current_time: datetime) -> Dict[str, Any]:
        """Analyze user's message pattern for flooding"""
        message_count = self.user_message_count[user_key]
        first_message_time = self.user_first_message_time[user_key]
        
        time_elapsed = (current_time - first_message_time).total_seconds()
        
        # Check per-second rate
        if time_elapsed > 0:
            messages_per_second = message_count / time_elapsed
            if messages_per_second > self.config["max_messages_per_second"]:
                return {
                    "is_flooding": True,
                    "reason": "high_message_rate",
                    "action": "mute",
                    "details": f"{messages_per_second:.1f} messages/second"
                }
                
        # Check per-minute rate (last 60 seconds)
        if time_elapsed < 60:
            if message_count > self.config["max_messages_per_minute"]:
                return {
                    "is_flooding": True,
                    "reason": "minute_limit_exceeded",
                    "action": "mute",
                    "details": f"{message_count} messages in {time_elapsed:.0f}s"
                }
        else:
            # Check rolling window for last minute
            # This would need timestamp tracking for each message
            # For now, use simple count reset approach
            pass
            
        # Check 5-minute limit
        if time_elapsed < 300:  # 5 minutes
            if message_count > self.config["max_messages_per_5minutes"]:
                return {
                    "is_flooding": True,
                    "reason": "five_minute_limit_exceeded",
                    "action": "mute",
                    "details": f"{message_count} messages in 5 minutes"
                }
                
        return {"is_flooding": False, "action": "allow"}
        
    def _check_inactivity(self, user_key: str, current_time: datetime):
        """Check and reset counters for inactive users"""
        if user_key in self.user_first_message_time:
            last_activity_age = (current_time - self.user_first_message_time[user_key]).total_seconds()
            
            # Reset if user has been inactive for auto_reset_time
            if last_activity_age > self.config["auto_reset_time"]:
                self._reset_user_counters(user_key)
                
    def _reset_user_counters(self, user_key: str):
        """Reset counters for user"""
        if user_key in self.user_message_count:
            del self.user_message_count[user_key]
        if user_key in self.user_first_message_time:
            del self.user_first_message_time[user_key]
            
    def _mute_user(self, user_key: str, duration: int, reason: str):
        """Mute user for specified duration"""
        self.muted_users[user_key] = {
            "muted_until": datetime.now() + timedelta(seconds=duration),
            "reason": reason,
            "muted_at": datetime.now(),
            "duration": duration
        }
        
        # Reset message counters
        self._reset_user_counters(user_key)
        
        self.logger.warning(f"🔇 Muted user {user_key} for {duration}s: {reason}")
        
    def _is_user_muted(self, user_key: str) -> bool:
        """Check if user is muted"""
        if user_key in self.muted_users:
            mute_data = self.muted_users[user_key]
            if datetime.now() < mute_data["muted_until"]:
                return True
            else:
                # Mute expired, remove
                del self.muted_users[user_key]
                return False
        return False
        
    def _get_mute_remaining(self, user_key: str) -> int:
        """Get remaining mute time in seconds"""
        if user_key in self.muted_users:
            mute_data = self.muted_users[user_key]
            remaining = (mute_data["muted_until"] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
        
    async def unmute_user(self, user_key: str) -> bool:
        """Unmute user"""
        if user_key in self.muted_users:
            del self.muted_users[user_key]
            self.logger.info(f"🔊 Unmuted user {user_key}")
            return True
        return False
        
    async def get_user_flood_stats(self, user_id: int, 
                                 group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user flood statistics"""
        user_key = self._get_user_key(user_id, group_id)
        
        stats = {
            "user_id": user_id,
            "group_id": group_id,
            "message_count": self.user_message_count.get(user_key, 0),
            "warnings": self.user_warnings.get(user_key, 0),
            "is_muted": self._is_user_muted(user_key),
            "mute_remaining": self._get_mute_remaining(user_key)
        }
        
        if user_key in self.user_first_message_time:
            first_msg_time = self.user_first_message_time[user_key]
            time_elapsed = (datetime.now() - first_msg_time).total_seconds()
            stats.update({
                "first_message_time": first_msg_time.isoformat(),
                "time_elapsed_seconds": time_elapsed,
                "messages_per_second": stats["message_count"] / time_elapsed if time_elapsed > 0 else 0
            })
            
        return stats
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get anti-flood system statistics"""
        currently_muted = sum(1 for mute_data in self.muted_users.values()
                             if datetime.now() < mute_data["muted_until"])
        
        return {
            "total_users_tracked": len(self.user_message_count),
            "currently_muted_users": currently_muted,
            "total_warnings_issued": sum(self.user_warnings.values()),
            "config": self.config
        }
        
    async def update_config(self, new_config: Dict[str, Any]):
        """Update anti-flood configuration"""
        self.config.update(new_config)
        self.logger.info(f"⚙️ Updated anti-flood config")
        
    async def reset_user(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """Reset all flood data for user"""
        user_key = self._get_user_key(user_id, group_id)
        
        self._reset_user_counters(user_key)
        
        if user_key in self.user_warnings:
            del self.user_warnings[user_key]
            
        await self.unmute_user(user_key)
        
        self.logger.info(f"🔄 Reset flood data for user {user_key}")
        return True