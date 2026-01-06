"""
Welcome Engine - Handles new member welcomes
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from core.utils.image_utils import create_welcome_image
from core.utils.voice_utils import generate_welcome_voice
from core.utils.time_utils import format_time, get_account_age

class WelcomeEngine:
    """Engine for welcoming new members"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_welcome")
        self.json_loader = json_loader
        self.welcome_cache = {}
        
    async def handle_new_member(self, user_data: Dict[str, Any], 
                               group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle new member welcome
        
        Args:
            user_data: User information
            group_data: Group information
            
        Returns:
            Response data
        """
        self.logger.info(f"👋 Welcoming new member: {user_data.get('username', 'Unknown')}")
        
        # Load welcome configuration
        welcome_config = await self.json_loader.load("responses/welcome.json")
        
        # Prepare response
        response = {
            "engine": "welcome",
            "type": "welcome_message",
            "user_id": user_data.get("id"),
            "group_id": group_data.get("id"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate welcome message
        welcome_message = await self._generate_welcome_message(user_data, group_data, welcome_config)
        response["message"] = welcome_message
        
        # Generate welcome image if enabled
        if welcome_config.get("image", True):
            image_path = await self._generate_welcome_image(user_data, group_data, welcome_config)
            if image_path:
                response["image"] = image_path
                
        # Generate welcome voice if enabled
        if welcome_config.get("voice", True):
            voice_path = await self._generate_welcome_voice(welcome_message, user_data)
            if voice_path:
                response["voice"] = voice_path
                
        # Add user to welcome cache
        cache_key = f"{user_data['id']}_{group_data['id']}"
        self.welcome_cache[cache_key] = {
            "welcome_time": datetime.now(),
            "message_sent": True
        }
        
        return response
        
    async def _generate_welcome_message(self, user_data: Dict, group_data: Dict, 
                                       config: Dict) -> str:
        """Generate welcome message"""
        # Load message templates
        templates = config.get("templates", [])
        
        if not templates:
            templates = [
                "🎉 স্বাগতম {user_name}!\n"
                "🌟 {group_name} গ্রুপে আপনাকে স্বাগতম!\n"
                "📊 গ্রুপ সদস্য: {total_members}\n"
                "🕐 যোগদান সময়: {join_time}\n"
                "📝 গ্রুপের নিয়মাবলী পড়ুন।"
            ]
            
        # Select random template
        import random
        template = random.choice(templates)
        
        # Prepare variables
        variables = {
            "user_name": user_data.get("first_name", "অতিথি"),
            "user_full_name": user_data.get("full_name", user_data.get("first_name", "অতিথি")),
            "user_id": user_data.get("id", "N/A"),
            "username": f"@{user_data.get('username', 'N/A')}" if user_data.get("username") else "N/A",
            "group_name": group_data.get("title", "এই গ্রুপ"),
            "total_members": group_data.get("member_count", "N/A"),
            "join_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "account_age": await get_account_age(user_data.get("id")),
            "bot_name": "𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬"
        }
        
        # Replace variables in template
        message = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            message = message.replace(placeholder, str(value))
            
        return message
        
    async def _generate_welcome_image(self, user_data: Dict, group_data: Dict, 
                                     config: Dict) -> Optional[str]:
        """Generate welcome image"""
        try:
            # Get user profile photo
            profile_photo = user_data.get("profile_photo")
            
            # Get group photo
            group_photo = group_data.get("photo")
            
            # Prepare image data
            image_data = {
                "user_name": user_data.get("first_name", "অতিথি"),
                "user_id": user_data.get("id"),
                "group_name": group_data.get("title", "গ্রুপ"),
                "member_count": group_data.get("member_count", 0),
                "join_date": datetime.now().strftime("%d %B %Y"),
                "join_time": datetime.now().strftime("%I:%M %p"),
                "profile_photo": profile_photo,
                "group_photo": group_photo,
                "template": config.get("image_template", "default")
            }
            
            # Create image
            image_path = await create_welcome_image(image_data)
            return image_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating welcome image: {e}")
            return None
            
    async def _generate_welcome_voice(self, message: str, user_data: Dict) -> Optional[str]:
        """Generate welcome voice message"""
        try:
            # Prepare voice data
            voice_data = {
                "text": message,
                "language": "bn",
                "voice_type": "soft",
                "speed": 1.0,
                "emotion": "happy"
            }
            
            # Generate voice
            voice_path = await generate_welcome_voice(voice_data)
            return voice_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating welcome voice: {e}")
            return None
            
    async def get_welcome_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get welcome statistics"""
        if group_id:
            group_welcomes = [w for w in self.welcome_cache.values() 
                             if w.get("group_id") == group_id]
            return {
                "group_id": group_id,
                "total_welcomes": len(group_welcomes),
                "today_welcomes": len([w for w in group_welcomes 
                                      if w["welcome_time"].date() == datetime.now().date()])
            }
        else:
            return {
                "total_welcomes": len(self.welcome_cache),
                "cache_size": len(self.welcome_cache)
            }
            
    def cleanup_old_welcomes(self, max_age_hours: int = 24):
        """Cleanup old welcome records"""
        current_time = datetime.now()
        old_keys = []
        
        for key, data in self.welcome_cache.items():
            if (current_time - data["welcome_time"]).total_seconds() > max_age_hours * 3600:
                old_keys.append(key)
                
        for key in old_keys:
            del self.welcome_cache[key]
            
        if old_keys:
            self.logger.info(f"🧹 Cleaned up {len(old_keys)} old welcome records")