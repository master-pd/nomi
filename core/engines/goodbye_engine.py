"""
Goodbye Engine - Handles member leave messages
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import random

from core.utils.voice_utils import generate_goodbye_voice

class GoodbyeEngine:
    """Engine for goodbye messages"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_goodbye")
        self.json_loader = json_loader
        self.leave_cache = {}
        
    async def handle_member_leave(self, user_data: Dict[str, Any], 
                                 group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle member leave
        
        Args:
            user_data: User information
            group_data: Group information
            
        Returns:
            Response data
        """
        self.logger.info(f"👋 Member left: {user_data.get('username', 'Unknown')}")
        
        # Load goodbye configuration
        goodbye_config = await self.json_loader.load("responses/goodbye.json")
        
        # Prepare response
        response = {
            "engine": "goodbye",
            "type": "goodbye_message",
            "user_id": user_data.get("id"),
            "group_id": group_data.get("id"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate goodbye message
        goodbye_message = await self._generate_goodbye_message(user_data, group_data, goodbye_config)
        response["message"] = goodbye_message
        
        # Generate goodbye voice if enabled
        if goodbye_config.get("voice", True):
            voice_path = await self._generate_goodbye_voice(goodbye_message, user_data)
            if voice_path:
                response["voice"] = voice_path
                
        # Cache leave
        cache_key = f"{user_data['id']}_{group_data['id']}"
        self.leave_cache[cache_key] = {
            "leave_time": datetime.now(),
            "user_name": user_data.get("first_name", "Unknown")
        }
        
        return response
        
    async def _generate_goodbye_message(self, user_data: Dict, group_data: Dict, 
                                       config: Dict) -> str:
        """Generate goodbye message"""
        # Load message templates
        templates = config.get("templates", [])
        
        if not templates:
            templates = [
                "👋 বিদায় {user_name}!\n"
                "আপনাকে {group_name} গ্রুপে পেয়ে ভালো লেগেছিল!\n"
                "ভবিষ্যতে আবার দেখা হবে আশা করি।",
                
                "🚶‍♂️ {user_name} গ্রুপ ছেড়ে চলে গেলেন।\n"
                "সফলতা আপনার সঙ্গী হোক!",
                
                "🌅 বিদায় নিলেন {user_name}...\n"
                "{group_name} পরিবার আপনাকে স্মরণ রাখবে।\n"
                "শুভ কামনা!"
            ]
            
        # Select random template
        template = random.choice(templates)
        
        # Prepare variables
        variables = {
            "user_name": user_data.get("first_name", "সদস্য"),
            "user_full_name": user_data.get("full_name", user_data.get("first_name", "সদস্য")),
            "user_id": user_data.get("id", "N/A"),
            "username": f"@{user_data.get('username', 'N/A')}" if user_data.get("username") else "N/A",
            "group_name": group_data.get("title", "এই গ্রুপ"),
            "leave_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_members": group_data.get("member_count", "N/A"),
            "bot_name": "𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬"
        }
        
        # Replace variables in template
        message = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            message = message.replace(placeholder, str(value))
            
        return message
        
    async def _generate_goodbye_voice(self, message: str, user_data: Dict) -> Optional[str]:
        """Generate goodbye voice message"""
        try:
            # Prepare voice data
            voice_data = {
                "text": message,
                "language": "bn",
                "voice_type": "soft",
                "speed": 0.9,
                "emotion": "sad"
            }
            
            # Generate voice
            from core.utils.voice_utils import generate_goodbye_voice as gen_voice
            voice_path = await gen_voice(voice_data)
            return voice_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating goodbye voice: {e}")
            return None
            
    async def handle_kick(self, user_data: Dict, group_data: Dict, 
                         kicked_by: Dict, reason: str = "") -> Dict[str, Any]:
        """
        Handle member kick
        
        Args:
            user_data: Kicked user information
            group_data: Group information
            kicked_by: Who kicked the user
            reason: Kick reason
            
        Returns:
            Response data
        """
        self.logger.warning(f"⚡ User kicked: {user_data.get('username', 'Unknown')}")
        
        response = {
            "engine": "goodbye",
            "type": "kick_message",
            "user_id": user_data.get("id"),
            "group_id": group_data.get("id"),
            "kicked_by": kicked_by.get("id"),
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate kick message
        kick_message = await self._generate_kick_message(user_data, kicked_by, reason)
        response["message"] = kick_message
        
        return response
        
    async def _generate_kick_message(self, user_data: Dict, kicked_by: Dict, 
                                    reason: str) -> str:
        """Generate kick message"""
        messages = [
            "⚡ {user_name} কে {kicked_by_name} দ্বারা গ্রুপ থেকে বের করে দেওয়া হয়েছে।\n"
            "কারণ: {reason}",
            
            "🚫 {user_name} গ্রুপ থেকে বাদ পড়েছেন।\n"
            "মডারেটর: {kicked_by_name}\n"
            "কারণ: {reason}",
            
            "🔴 {user_name} এর গ্রুপ এক্সেস বাতিল করা হয়েছে।\n"
            "কারণ: {reason}"
        ]
        
        template = random.choice(messages)
        
        variables = {
            "user_name": user_data.get("first_name", "সদস্য"),
            "user_id": user_data.get("id"),
            "kicked_by_name": kicked_by.get("first_name", "মডারেটর"),
            "kicked_by_id": kicked_by.get("id"),
            "reason": reason or "নির্দিষ্ট করা হয়নি",
            "time": datetime.now().strftime("%H:%M")
        }
        
        message = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            message = message.replace(placeholder, str(value))
            
        return message
        
    async def get_leave_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get leave statistics"""
        if group_id:
            group_leaves = [l for l in self.leave_cache.values() 
                           if l.get("group_id") == group_id]
            return {
                "group_id": group_id,
                "total_leaves": len(group_leaves),
                "today_leaves": len([l for l in group_leaves 
                                    if l["leave_time"].date() == datetime.now().date()])
            }
        else:
            return {
                "total_leaves": len(self.leave_cache),
                "cache_size": len(self.leave_cache)
            }
            
    def cleanup_old_leaves(self, max_age_hours: int = 24):
        """Cleanup old leave records"""
        current_time = datetime.now()
        old_keys = []
        
        for key, data in self.leave_cache.items():
            if (current_time - data["leave_time"]).total_seconds() > max_age_hours * 3600:
                old_keys.append(key)
                
        for key in old_keys:
            del self.leave_cache[key]
            
        if old_keys:
            self.logger.info(f"🧹 Cleaned up {len(old_keys)} old leave records")