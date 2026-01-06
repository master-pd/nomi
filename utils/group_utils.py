"""
Group management utilities
"""

import logging
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.types import Chat

from config import Config
from utils.json_utils import JSONManager

logger = logging.getLogger(__name__)
json_manager = JSONManager()

class GroupUtils:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.json_manager = JSONManager()
    
    async def get_group_info(self, group_id: int) -> Optional[Dict]:
        """
        Get group information
        """
        try:
            chat = await self.bot.get_chat(group_id)
            
            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "description": chat.description,
                "member_count": await chat.get_member_count()
            }
        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            return None
    
    async def get_all_bot_groups(self) -> List[Dict]:
        """
        Get all groups where bot is a member
        """
        # Note: This requires bot to be admin in groups
        # You might need to store groups in database when bot is added
        
        groups = self.json_manager.get_all_groups()
        detailed_groups = []
        
        for group in groups:
            group_id = group.get("id")
            if group_id:
                group_info = await self.get_group_info(group_id)
                if group_info:
                    detailed_groups.append({**group, **group_info})
        
        return detailed_groups
    
    async def invite_bot_to_group(self, group_id: int) -> str:
        """
        Generate invite link for specific group
        """
        try:
            # Create invite link
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=group_id,
                member_limit=1,
                name="Bot Invite"
            )
            return invite_link.invite_link
        except Exception as e:
            logger.error(f"Error creating invite link: {e}")
            return Config.INVITE_LINK
    
    def format_group_list(self, groups: List[Dict]) -> str:
        """
        Format group list for display
        """
        if not groups:
            return "📭 কোনো গ্রুপ পাওয়া যায়নি।"
        
        formatted = "📋 **গ্রুপ লিস্ট:**\n\n"
        
        for i, group in enumerate(groups, start=1):
            title = group.get('title', 'Unknown Group')
            members = group.get('member_count', 0)
            messages = group.get('total_messages', 0)
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   👥 {members} সদস্য | 💬 {messages} মেসেজ\n"
            
            if group.get('username'):
                formatted += f"   🔗 @{group['username']}\n"
            
            formatted += "\n"
        
        return formatted
    
    async def update_group_stats(self, group_id: int):
        """
        Update group statistics
        """
        group_info = await self.get_group_info(group_id)
        if not group_info:
            return
        
        current_data = self.json_manager.get_group(group_id) or {}
        
        updated_data = {
            **current_data,
            **group_info,
            "last_updated": Config.get_current_time(),
            "member_count": group_info.get('member_count', current_data.get('member_count', 0))
        }
        
        self.json_manager.update_group(group_id, updated_data)
        logger.info(f"Updated stats for group: {group_id}")