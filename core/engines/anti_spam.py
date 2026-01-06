"""
Anti-Spam System - Detects and prevents spam messages
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class AntiSpam:
    """Anti-spam detection system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_antispam")
        self.user_message_times = defaultdict(list)
        self.user_message_content = defaultdict(list)
        self.spam_detections = defaultdict(int)
        self.muted_users = {}
        
        # Configuration
        self.config = {
            "max_messages_per_minute": 10,
            "max_similar_messages": 3,
            "min_message_interval": 2,  # seconds
            "spam_threshold": 5,
            "mute_duration": 300,  # 5 minutes
            "auto_mute_enabled": True,
            "similarity_threshold": 0.8
        }
        
    async def check_message(self, user_id: int, message: str, 
                          group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Check message for spam
        
        Args:
            user_id: User ID
            message: Message content
            group_id: Group ID
            
        Returns:
            Spam check result
        """
        current_time = datetime.now()
        
        # Check if user is muted
        if self._is_user_muted(user_id, group_id):
            return {
                "is_spam": True,
                "reason": "user_muted",
                "action": "delete",
                "mute_remaining": self._get_mute_remaining(user_id, group_id)
            }
            
        # Clean old message records
        self._clean_old_records(user_id)
        
        # Check message rate
        rate_check = await self._check_message_rate(user_id, current_time)
        if rate_check["is_spam"]:
            self._record_spam_detection(user_id, group_id)
            return rate_check
            
        # Check message similarity
        similarity_check = await self._check_message_similarity(user_id, message)
        if similarity_check["is_spam"]:
            self._record_spam_detection(user_id, group_id)
            return similarity_check
            
        # Check character patterns
        pattern_check = await self._check_patterns(message)
        if pattern_check["is_spam"]:
            self._record_spam_detection(user_id, group_id)
            return pattern_check
            
        # Record message (not spam)
        self.user_message_times[user_id].append(current_time)
        self.user_message_content[user_id].append({
            "message": message,
            "time": current_time,
            "group_id": group_id
        })
        
        # Keep only recent messages
        self.user_message_content[user_id] = self.user_message_content[user_id][-20:]
        
        return {
            "is_spam": False,
            "reason": "",
            "action": "allow"
        }
        
    async def _check_message_rate(self, user_id: int, current_time: datetime) -> Dict[str, Any]:
        """Check message rate for spam"""
        user_messages = self.user_message_times.get(user_id, [])
        
        # Count messages in last minute
        one_minute_ago = current_time - timedelta(minutes=1)
        recent_messages = [msg_time for msg_time in user_messages 
                          if msg_time > one_minute_ago]
        
        if len(recent_messages) >= self.config["max_messages_per_minute"]:
            return {
                "is_spam": True,
                "reason": "message_rate",
                "action": "mute",
                "details": f"{len(recent_messages)} messages in last minute",
                "mute_duration": self.config["mute_duration"]
            }
            
        # Check minimum interval
        if user_messages:
            last_message_time = user_messages[-1]
            time_diff = (current_time - last_message_time).total_seconds()
            
            if time_diff < self.config["min_message_interval"]:
                return {
                    "is_spam": True,
                    "reason": "message_interval",
                    "action": "warn",
                    "details": f"Messages too fast: {time_diff:.1f}s interval"
                }
                
        return {"is_spam": False}
        
    async def _check_message_similarity(self, user_id: int, new_message: str) -> Dict[str, Any]:
        """Check for similar messages"""
        user_messages = self.user_message_content.get(user_id, [])
        
        if not user_messages:
            return {"is_spam": False}
            
        # Get recent messages (last 10)
        recent_messages = user_messages[-10:]
        
        # Check similarity with recent messages
        similar_count = 0
        for msg_data in recent_messages:
            similarity = self._calculate_similarity(new_message, msg_data["message"])
            if similarity > self.config["similarity_threshold"]:
                similar_count += 1
                
        if similar_count >= self.config["max_similar_messages"]:
            return {
                "is_spam": True,
                "reason": "similar_messages",
                "action": "mute",
                "details": f"{similar_count} similar messages detected",
                "mute_duration": self.config["mute_duration"]
            }
            
        return {"is_spam": False}
        
    async def _check_patterns(self, message: str) -> Dict[str, Any]:
        """Check for spam patterns"""
        # Check for excessive repetition
        if self._has_excessive_repetition(message):
            return {
                "is_spam": True,
                "reason": "excessive_repetition",
                "action": "delete"
            }
            
        # Check for excessive capitalization
        if self._has_excessive_caps(message):
            return {
                "is_spam": True,
                "reason": "excessive_caps",
                "action": "warn"
            }
            
        # Check for common spam words/phrases
        spam_phrases = [
            "বিনা পয়সায়", "ফ্রি", "মাত্র ১০০ টাকায়",
            "ক্লিক করুন", "লিংক", "ভিসিট করুন",
            "$$$", "মেক মানি", "ইনকাম"
        ]
        
        message_lower = message.lower()
        for phrase in spam_phrases:
            if phrase in message_lower:
                return {
                    "is_spam": True,
                    "reason": "spam_phrase",
                    "action": "delete",
                    "details": f"Contains spam phrase: {phrase}"
                }
                
        return {"is_spam": False}
        
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple similarity calculation
        if not str1 or not str2:
            return 0.0
            
        # Convert to sets of words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
        
    def _has_excessive_repetition(self, message: str) -> bool:
        """Check for excessive character repetition"""
        if len(message) < 10:
            return False
            
        # Check for repeated characters
        for i in range(len(message) - 5):
            if message[i] == message[i+1] == message[i+2] == message[i+3] == message[i+4]:
                return True
                
        # Check for repeated words
        words = message.split()
        if len(words) >= 3:
            for i in range(len(words) - 2):
                if words[i] == words[i+1] == words[i+2]:
                    return True
                    
        return False
        
    def _has_excessive_caps(self, message: str) -> bool:
        """Check for excessive capitalization"""
        if len(message) < 10:
            return False
            
        # Count uppercase letters
        upper_count = sum(1 for c in message if c.isupper())
        upper_ratio = upper_count / len(message)
        
        return upper_ratio > 0.5 and upper_count > 10
        
    def _record_spam_detection(self, user_id: int, group_id: Optional[int]):
        """Record spam detection for user"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        self.spam_detections[key] += 1
        
        # Auto-mute if threshold reached
        if (self.config["auto_mute_enabled"] and 
            self.spam_detections[key] >= self.config["spam_threshold"]):
            self._mute_user(user_id, group_id, self.config["mute_duration"])
            
    def _mute_user(self, user_id: int, group_id: Optional[int], duration: int):
        """Mute user for specified duration"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        self.muted_users[key] = {
            "muted_until": datetime.now() + timedelta(seconds=duration),
            "reason": "spam",
            "muted_at": datetime.now()
        }
        
        self.logger.warning(f"🔇 Muted user {user_id} for {duration}s (spam)")
        
    def _is_user_muted(self, user_id: int, group_id: Optional[int]) -> bool:
        """Check if user is muted"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if key in self.muted_users:
            mute_data = self.muted_users[key]
            if datetime.now() < mute_data["muted_until"]:
                return True
            else:
                # Mute expired, remove
                del self.muted_users[key]
                
        return False
        
    def _get_mute_remaining(self, user_id: int, group_id: Optional[int]) -> int:
        """Get remaining mute time in seconds"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if key in self.muted_users:
            mute_data = self.muted_users[key]
            remaining = (mute_data["muted_until"] - datetime.now()).total_seconds()
            return max(0, int(remaining))
            
        return 0
        
    def _clean_old_records(self, user_id: int):
        """Clean old message records for user"""
        current_time = datetime.now()
        
        # Clean message times (keep last hour)
        if user_id in self.user_message_times:
            one_hour_ago = current_time - timedelta(hours=1)
            self.user_message_times[user_id] = [
                t for t in self.user_message_times[user_id] 
                if t > one_hour_ago
            ]
            
        # Clean message content (keep last hour)
        if user_id in self.user_message_content:
            one_hour_ago = current_time - timedelta(hours=1)
            self.user_message_content[user_id] = [
                m for m in self.user_message_content[user_id]
                if m["time"] > one_hour_ago
            ]
            
    async def unmute_user(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """Unmute user"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if key in self.muted_users:
            del self.muted_users[key]
            self.logger.info(f"🔊 Unmuted user {user_id}")
            return True
            
        return False
        
    async def get_user_spam_stats(self, user_id: int, 
                                group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user spam statistics"""
        key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        return {
            "user_id": user_id,
            "group_id": group_id,
            "spam_detections": self.spam_detections.get(key, 0),
            "is_muted": self._is_user_muted(user_id, group_id),
            "mute_remaining": self._get_mute_remaining(user_id, group_id),
            "recent_messages": len(self.user_message_times.get(user_id, [])),
            "message_rate": self._calculate_message_rate(user_id)
        }
        
    def _calculate_message_rate(self, user_id: int) -> float:
        """Calculate user's message rate (messages per minute)"""
        user_messages = self.user_message_times.get(user_id, [])
        
        if not user_messages:
            return 0.0
            
        current_time = datetime.now()
        one_minute_ago = current_time - timedelta(minutes=1)
        
        recent_count = sum(1 for t in user_messages if t > one_minute_ago)
        return recent_count
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get anti-spam system statistics"""
        total_detections = sum(self.spam_detections.values())
        currently_muted = sum(1 for mute_data in self.muted_users.values()
                             if datetime.now() < mute_data["muted_until"])
        
        return {
            "total_users_tracked": len(self.user_message_times),
            "total_spam_detections": total_detections,
            "currently_muted_users": currently_muted,
            "total_muted_users": len(self.muted_users),
            "config": self.config
        }
        
    async def update_config(self, new_config: Dict[str, Any]):
        """Update anti-spam configuration"""
        self.config.update(new_config)
        self.logger.info(f"⚙️ Updated anti-spam config: {new_config}")