"""
Auto Reply Engine - Handles automatic responses
"""

import re
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from core.utils.string_utils import normalize_bangla_text

class AutoReplyEngine:
    """Engine for automatic replies"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_autoreply")
        self.json_loader = json_loader
        self.reply_patterns = {}
        self.conversation_context = {}
        self.message_history = {}
        
    async def initialize(self):
        """Initialize auto reply engine"""
        self.logger.info("💬 Initializing auto reply engine...")
        await self._load_reply_patterns()
        
    async def _load_reply_patterns(self):
        """Load reply patterns from JSON"""
        reply_config = await self.json_loader.load("responses/auto_reply.json")
        self.reply_patterns = reply_config.get("patterns", {})
        self.logger.info(f"📝 Loaded {len(self.reply_patterns)} reply patterns")
        
    async def handle_message(self, message: str, user_id: int, 
                           group_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Handle incoming message and generate reply
        
        Args:
            message: Message text
            user_id: User ID
            group_id: Group ID
            
        Returns:
            Reply data or None
        """
        if not message or not message.strip():
            return None
            
        # Normalize message for better matching
        normalized_msg = normalize_bangla_text(message.strip().lower())
        
        # Check for patterns
        reply_data = await self._match_pattern(normalized_msg, user_id, group_id)
        
        if reply_data:
            # Update conversation context
            await self._update_context(user_id, message, reply_data.get("response"))
            
            # Prepare response
            response = {
                "engine": "auto_reply",
                "type": "text_reply",
                "user_id": user_id,
                "group_id": group_id,
                "original_message": message,
                "reply": reply_data.get("response"),
                "confidence": reply_data.get("confidence", 0.5),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add voice if configured
            if reply_data.get("voice"):
                response["voice"] = reply_data["voice"]
                
            return response
            
        # Fallback to generic response
        return await self._generate_fallback_response(message, user_id, group_id)
        
    async def _match_pattern(self, message: str, user_id: int, 
                           group_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """
        Match message against reply patterns
        
        Args:
            message: Normalized message
            user_id: User ID
            group_id: Group ID
            
        Returns:
            Matched reply data
        """
        best_match = None
        best_score = 0
        
        for pattern_id, pattern_data in self.reply_patterns.items():
            patterns = pattern_data.get("patterns", [])
            response = pattern_data.get("response")
            voice = pattern_data.get("voice")
            
            if not patterns or not response:
                continue
                
            # Check each pattern
            for pattern in patterns:
                score = await self._calculate_match_score(message, pattern, pattern_data)
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "pattern_id": pattern_id,
                        "response": response,
                        "voice": voice,
                        "confidence": score,
                        "pattern_data": pattern_data
                    }
                    
        # Only return if score is above threshold
        if best_score > 0.6:  # 60% match threshold
            return best_match
            
        return None
        
    async def _calculate_match_score(self, message: str, pattern: str, 
                                   pattern_data: Dict) -> float:
        """
        Calculate match score between message and pattern
        
        Args:
            message: User message
            pattern: Pattern to match
            pattern_data: Pattern metadata
            
        Returns:
            Match score 0-1
        """
        # Exact match
        if message == pattern.lower():
            return 1.0
            
        # Contains match
        if pattern.lower() in message:
            return 0.8
            
        # Regex match
        try:
            if re.search(pattern, message, re.IGNORECASE):
                return 0.9
        except:
            pass
            
        # Word-based match
        message_words = set(message.split())
        pattern_words = set(pattern.lower().split())
        
        if pattern_words:
            intersection = message_words.intersection(pattern_words)
            score = len(intersection) / len(pattern_words)
            return score * 0.7  # Weight for word matches
            
        return 0.0
        
    async def _generate_fallback_response(self, message: str, user_id: int,
                                        group_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """Generate fallback response when no pattern matches"""
        # Load fallback responses
        reply_config = await self.json_loader.load("responses/auto_reply.json")
        fallbacks = reply_config.get("fallback_responses", [])
        
        if not fallbacks:
            fallbacks = [
                "আমি এখনো শিখছি, আপনি অন্য কিছু জিজ্ঞাসা করতে পারেন।",
                "দুঃখিত, আমি এই প্রশ্নের উত্তর জানি না।",
                "এখনো এই বিষয়ে আমার জ্ঞান নেই।",
                "আমাকে আরো স্মার্ট হতে হবে এই প্রশ্নের জন্য!"
            ]
            
        # Check conversation context
        context = self.conversation_context.get(user_id, {})
        
        # If user is asking repeatedly, give different response
        if context.get("repeat_count", 0) > 2:
            response = "আপনি একই প্রশ্ন বারবার করছেন। অন্য কিছু জিজ্ঞাসা করুন।"
        else:
            response = random.choice(fallbacks)
            
        # Prepare response
        return {
            "engine": "auto_reply",
            "type": "fallback_reply",
            "user_id": user_id,
            "group_id": group_id,
            "original_message": message,
            "reply": response,
            "confidence": 0.1,
            "timestamp": datetime.now().isoformat(),
            "is_fallback": True
        }
        
    async def _update_context(self, user_id: int, user_message: str, bot_reply: str):
        """Update conversation context"""
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = {
                "last_message": user_message,
                "last_reply": bot_reply,
                "repeat_count": 0,
                "message_count": 0,
                "last_interaction": datetime.now()
            }
        else:
            context = self.conversation_context[user_id]
            
            # Check if same message
            if user_message == context.get("last_message"):
                context["repeat_count"] += 1
            else:
                context["repeat_count"] = 0
                
            context["last_message"] = user_message
            context["last_reply"] = bot_reply
            context["message_count"] += 1
            context["last_interaction"] = datetime.now()
            
        # Cleanup old contexts
        self._cleanup_old_contexts()
        
    def _cleanup_old_contexts(self, max_age_minutes: int = 60):
        """Cleanup old conversation contexts"""
        current_time = datetime.now()
        old_users = []
        
        for user_id, context in self.conversation_context.items():
            last_interaction = context.get("last_interaction")
            if last_interaction and (current_time - last_interaction).total_seconds() > max_age_minutes * 60:
                old_users.append(user_id)
                
        for user_id in old_users:
            del self.conversation_context[user_id]
            
    async def add_pattern(self, pattern: str, response: str, 
                         pattern_type: str = "text", voice: Optional[str] = None):
        """
        Add new reply pattern
        
        Args:
            pattern: Pattern to match
            response: Response text
            pattern_type: Type of pattern
            voice: Voice response path
        """
        pattern_id = f"custom_{int(datetime.now().timestamp())}"
        
        new_pattern = {
            "patterns": [pattern],
            "response": response,
            "type": pattern_type,
            "voice": voice,
            "created_at": datetime.now().isoformat()
        }
        
        self.reply_patterns[pattern_id] = new_pattern
        
        # Save to JSON
        await self._save_patterns()
        
        self.logger.info(f"➕ Added new pattern: {pattern_id}")
        
    async def _save_patterns(self):
        """Save patterns to JSON"""
        try:
            reply_config = await self.json_loader.load("responses/auto_reply.json")
            reply_config["patterns"] = self.reply_patterns
            
            await self.json_loader.save("responses/auto_reply.json", reply_config)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving patterns: {e}")
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "total_patterns": len(self.reply_patterns),
            "active_contexts": len(self.conversation_context),
            "message_history_size": len(self.message_history),
            "patterns_by_type": self._count_patterns_by_type()
        }
        
    def _count_patterns_by_type(self) -> Dict[str, int]:
        """Count patterns by type"""
        type_count = {}
        for pattern_data in self.reply_patterns.values():
            ptype = pattern_data.get("type", "text")
            type_count[ptype] = type_count.get(ptype, 0) + 1
        return type_count
        
    async def train_from_conversation(self, user_message: str, bot_reply: str):
        """
        Train engine from conversation
        
        Args:
            user_message: User message
            bot_reply: Bot reply
        """
        # Simple training - add pattern if not exists
        normalized_msg = normalize_bangla_text(user_message.strip().lower())
        
        # Check if similar pattern exists
        exists = False
        for pattern_data in self.reply_patterns.values():
            patterns = pattern_data.get("patterns", [])
            if any(normalized_msg in p.lower() or p.lower() in normalized_msg for p in patterns):
                exists = True
                break
                
        if not exists:
            await self.add_pattern(user_message, bot_reply)
            self.logger.info(f"🎓 Trained from conversation: {user_message[:50]}...")