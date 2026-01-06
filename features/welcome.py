"""
Professional Welcome System for Your Crush Bot
With image collage, voice welcome, dynamic overlays, and more
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Tuple, Union
from aiogram import Bot
from aiogram.types import (
    ChatMemberUpdated, 
    InputFile, 
    FSInputFile,
    Message
)

from config import Config
from utils.json_utils import JSONManager
from utils.image_utils import ImageUtils
from utils.voice_utils import VoiceUtils
from utils.time_utils import TimeUtils
from features.badges import BadgeSystem

logger = logging.getLogger(__name__)
json_manager = JSONManager()
image_utils = ImageUtils()
voice_utils = VoiceUtils()
time_utils = TimeUtils()
badge_system = BadgeSystem()

class WelcomeSystem:
    """Professional welcome system with all features"""
    
    def __init__(self):
        self.wg_config = self._load_wg_config()
        self.default_config = self._load_default_config()
        
    def _load_wg_config(self) -> Dict:
        """Load welcome/goodbye configuration"""
        try:
            import json
            if os.path.exists(Config.WG_JSON):
                with open(Config.WG_JSON, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading WG config: {e}")
            return {}
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        try:
            import json
            if os.path.exists(Config.DEFAULT_JSON):
                with open(Config.DEFAULT_JSON, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading default config: {e}")
            return {}
    
    async def handle_welcome(self, bot: Bot, event: ChatMemberUpdated):
        """
        Handle new member welcome
        """
        try:
            user = event.new_chat_member.user
            chat = event.chat
            user_id = user.id
            chat_id = chat.id
            
            logger.info(f"New member joined: {user_id} in chat {chat_id}")
            
            # Check if user is a bot
            if user.is_bot:
                await self._handle_bot_join(bot, user, chat)
                return
            
            # Update user data
            await self._update_user_data(user, chat_id)
            
            # Update group data
            await self._update_group_data(chat)
            
            # Generate welcome content
            welcome_content = await self._generate_welcome_content(user, chat)
            
            # Send welcome message
            await self._send_welcome_message(bot, chat_id, welcome_content)
            
            # Award welcome badge
            badge_system.check_and_award_badges(user_id, "user_joined", {
                "chat_id": chat_id,
                "is_first_join": True
            })
            
            # Log the welcome
            self._log_welcome_event(user_id, chat_id)
            
            logger.info(f"Welcome completed for user {user_id} in chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error in welcome handler: {e}")
    
    async def _handle_bot_join(self, bot: Bot, user: dict, chat: dict):
        """Handle bot join event"""
        try:
            # Check if joined bot is our bot
            if user.id == Config.BOT_ID:
                await self._send_bot_welcome(bot, chat)
            else:
                # Another bot joined
                await self._handle_other_bot_join(bot, user, chat)
                
        except Exception as e:
            logger.error(f"Error handling bot join: {e}")
    
    async def _send_bot_welcome(self, bot: Bot, chat: dict):
        """Send welcome message when bot joins a group"""
        try:
            welcome_text = """
            🤖 **Your Crush Bot যোগদান করেছে!**
            
            ধন্যবাদ আমাকে এই গ্রুপে অ্যাড করার জন্য।
            
            **আমার ফিচারসমূহ:**
            ✅ অটো ওয়েলকাম মেসেজ
            ✅ গ্রুপ মডারেশন
            ✅ ইউজার র‍্যাংকিং
            ✅ বাংলা ভয়েস রিপ্লাই
            ✅ ইভেন্ট ট্রিগার
            
            **কমান্ডসমূহ:**
            /start - বট শুরু করুন
            /help - সাহায্য দেখুন
            /menu - মেনু দেখুন
            /rules - গ্রুপ নিয়ম
            
            আমাকে এডমিন করুন সব ফিচার পেতে।
            """
            
            await bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error sending bot welcome: {e}")
    
    async def _handle_other_bot_join(self, bot: Bot, user: dict, chat: dict):
        """Handle when another bot joins the group"""
        try:
            # You can add special handling for other bots
            # For now, just log it
            logger.info(f"Other bot joined: @{user.username} in chat {chat.id}")
            
        except Exception as e:
            logger.error(f"Error handling other bot join: {e}")
    
    async def _update_user_data(self, user: dict, chat_id: int):
        """Update user data in database"""
        try:
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "join_date": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "joined_groups": json_manager.get_user_stat(user.id, "joined_groups", []) + [chat_id]
            }
            
            # Increment join count
            join_count = json_manager.get_user_stat(user.id, "join_count", 0)
            user_data["join_count"] = join_count + 1
            
            # Check if first join
            if join_count == 0:
                user_data["is_first_join"] = True
            else:
                user_data["is_first_join"] = False
            
            json_manager.update_user(user.id, user_data)
            
        except Exception as e:
            logger.error(f"Error updating user data: {e}")
    
    async def _update_group_data(self, chat: dict):
        """Update group data in database"""
        try:
            group_data = {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "member_count": await chat.get_member_count(),
                "last_activity": datetime.now().isoformat(),
                "welcome_count": json_manager.get_group_stat(chat.id, "welcome_count", 0) + 1
            }
            
            json_manager.update_group(chat.id, group_data)
            
        except Exception as e:
            logger.error(f"Error updating group data: {e}")
    
    async def _generate_welcome_content(self, user: dict, chat: dict) -> Dict:
        """Generate all welcome content (text, image, voice)"""
        try:
            # Get user and group info
            user_info = json_manager.get_user(user.id) or {}
            group_info = json_manager.get_group(chat.id) or {}
            
            # Prepare data for templates
            welcome_data = self._prepare_welcome_data(user, chat, user_info, group_info)
            
            # Generate text
            welcome_text = self._generate_welcome_text(welcome_data)
            
            # Generate image collage
            welcome_image = await self._generate_welcome_image(welcome_data)
            
            # Generate voice message
            welcome_voice = await self._generate_welcome_voice(welcome_data)
            
            # Generate inline buttons
            inline_buttons = self._generate_welcome_buttons(user.id, chat.id)
            
            return {
                "text": welcome_text,
                "image": welcome_image,
                "voice": welcome_voice,
                "buttons": inline_buttons,
                "data": welcome_data
            }
            
        except Exception as e:
            logger.error(f"Error generating welcome content: {e}")
            return {}
    
    def _prepare_welcome_data(self, user: dict, chat: dict, user_info: Dict, group_info: Dict) -> Dict:
        """Prepare data for welcome templates"""
        try:
            # Get account age
            account_age = time_utils.get_account_age(user.id)
            
            # Get join time in Bangladesh timezone
            join_time = time_utils.get_current_time_bd()
            
            # Calculate member serial number
            member_count = group_info.get("member_count", 0)
            member_serial = member_count
            
            # Get user rank
            rank = user_info.get("rank", "নতুন")
            
            # Get reputation
            reputation = user_info.get("reputation", 0)
            
            # Get group rules
            rules = self.wg_config.get("welcome", {}).get("rules", [])
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    "mention": f"[{user.first_name}](tg://user?id={user.id})",
                    "account_age": account_age,
                    "rank": rank,
                    "reputation": reputation,
                    "language": user.language_code or "en",
                    "is_bot": user.is_bot,
                    "join_count": user_info.get("join_count", 1),
                    "is_first_join": user_info.get("is_first_join", True)
                },
                "group": {
                    "id": chat.id,
                    "title": chat.title,
                    "username": chat.username,
                    "member_count": member_count,
                    "member_serial": member_serial,
                    "type": chat.type,
                    "rules": rules,
                    "security": "High",  # Placeholder
                    "level": group_info.get("level", 1)
                },
                "time": {
                    "join_time": join_time.strftime("%I:%M %p"),
                    "join_date": join_time.strftime("%d %B, %Y"),
                    "day_name": time_utils.get_day_name_bd(),
                    "timestamp": datetime.now().isoformat()
                },
                "bot": {
                    "name": Config.BOT_NAME,
                    "username": Config.BOT_USERNAME,
                    "version": "1.0.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Error preparing welcome data: {e}")
            return {}
    
    def _generate_welcome_text(self, welcome_data: Dict) -> str:
        """Generate welcome text"""
        try:
            # Get template from config or use default
            template = self.wg_config.get("welcome", {}).get("text", "")
            
            if not template:
                # Default template
                template = """আসসালামু আলাইকুম {user_full_name} 🌸

{group_title} গ্রুপে আপনাকে স্বাগতম!

📊 **আপনার তথ্য:**
👤 নাম: {user_full_name}
🆔 আইডি: `{user_id}`
📅 যোগদান: {join_date} ({join_time})
🏆 র‍্যাংক: {user_rank}
⭐ রিপুটেশন: {user_reputation}
👥 সিরিয়াল: {member_serial}/{member_count}

📜 **গ্রুপের নিয়ম:**
{group_rules}

বট সম্পর্কে জানতে /menu কমান্ড দিন।"""
            
            # Replace placeholders
            text = self._replace_placeholders(template, welcome_data)
            
            # Add gradient/shadows if enabled
            if self.wg_config.get("welcome", {}).get("gradient_text", True):
                text = self._apply_text_effects(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error generating welcome text: {e}")
            return "গ্রুপে আপনাকে স্বাগতম! 🎉"
    
    def _replace_placeholders(self, text: str, data: Dict) -> str:
        """Replace placeholders in text with actual data"""
        try:
            # User placeholders
            text = text.replace("{name}", data["user"]["full_name"])
            text = text.replace("{user_full_name}", data["user"]["full_name"])
            text = text.replace("{user_first_name}", data["user"]["first_name"] or "")
            text = text.replace("{user_last_name}", data["user"]["last_name"] or "")
            text = text.replace("{user_username}", f"@{data['user']['username']}" if data["user"]["username"] else "N/A")
            text = text.replace("{user_id}", str(data["user"]["id"]))
            text = text.replace("{user_rank}", data["user"]["rank"])
            text = text.replace("{user_reputation}", str(data["user"]["reputation"]))
            text = text.replace("{user_mention}", data["user"]["mention"])
            text = text.replace("{account_age}", data["user"]["account_age"])
            text = text.replace("{user_language}", data["user"]["language"])
            
            # Group placeholders
            text = text.replace("{group}", data["group"]["title"])
            text = text.replace("{group_title}", data["group"]["title"])
            text = text.replace("{group_username}", f"@{data['group']['username']}" if data["group"]["username"] else "N/A")
            text = text.replace("{group_id}", str(data["group"]["id"]))
            text = text.replace("{total_members}", str(data["group"]["member_count"]))
            text = text.replace("{member_count}", str(data["group"]["member_count"]))
            text = text.replace("{sirial_number}", str(data["group"]["member_serial"]))
            text = text.replace("{member_serial}", str(data["group"]["member_serial"]))
            
            # Time placeholders
            text = text.replace("{join_time}", data["time"]["join_time"])
            text = text.replace("{join_date}", data["time"]["join_date"])
            text = text.replace("{join_date_time}", f"{data['time']['join_date']} {data['time']['join_time']}")
            text = text.replace("{day_name}", data["time"]["day_name"])
            
            # Rules placeholder
            rules_text = "\n".join([f"• {rule}" for rule in data["group"]["rules"]])
            text = text.replace("{group_rules}", rules_text)
            text = text.replace("{rules}", rules_text)
            
            # Bot placeholders
            text = text.replace("{bot_name}", data["bot"]["name"])
            text = text.replace("{bot_username}", f"@{data['bot']['username']}")
            
            return text
            
        except Exception as e:
            logger.error(f"Error replacing placeholders: {e}")
            return text
    
    def _apply_text_effects(self, text: str) -> str:
        """Apply text effects like gradient/shadow"""
        # This is a simplified version
        # In production, you might want to use HTML or Markdown effects
        
        # Add some emojis and formatting
        lines = text.split("\n")
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith("👤"):
                formatted_lines.append(f"✨ **{line}**")
            elif line.strip().startswith("🆔"):
                formatted_lines.append(f"🔐 `{line[3:]}`")
            elif line.strip().startswith("📅"):
                formatted_lines.append(f"🗓️ {line}")
            elif line.strip().startswith("🏆"):
                formatted_lines.append(f"🎖️ {line}")
            elif line.strip().startswith("⭐"):
                formatted_lines.append(f"💫 {line}")
            elif line.strip().startswith("👥"):
                formatted_lines.append(f"👥 {line}")
            elif line.strip().startswith("📜"):
                formatted_lines.append(f"📋 **{line}**")
            elif line.strip().startswith("•"):
                formatted_lines.append(f"▪️ {line[2:]}")
            else:
                formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    async def _generate_welcome_image(self, welcome_data: Dict) -> Optional[str]:
        """Generate welcome image collage"""
        try:
            # Check if image collage is enabled
            if not self.wg_config.get("welcome", {}).get("image_collage", True):
                return None
            
            # Get user profile photo
            profile_photo = await self._get_user_profile_photo(welcome_data["user"]["id"])
            
            # Get group photo
            group_photo = await self._get_group_photo(welcome_data["group"]["id"])
            
            # Create collage
            collage_path = image_utils.create_welcome_collage(
                profile_image=profile_photo,
                group_image=group_photo,
                user_info=welcome_data["user"],
                group_info=welcome_data["group"]
            )
            
            return collage_path
            
        except Exception as e:
            logger.error(f"Error generating welcome image: {e}")
            return None
    
    async def _get_user_profile_photo(self, user_id: int) -> Optional[str]:
        """Get user profile photo URL"""
        try:
            # This would require bot to have access to user profile photos
            # For now, return default or placeholder
            
            # Check if we have a cached photo URL
            user_data = json_manager.get_user(user_id)
            if user_data and user_data.get("profile_photo"):
                return user_data["profile_photo"]
            
            # Return default profile image
            return Config.DEFAULT_PROFILE
            
        except Exception as e:
            logger.error(f"Error getting user profile photo: {e}")
            return Config.DEFAULT_PROFILE
    
    async def _get_group_photo(self, group_id: int) -> Optional[str]:
        """Get group photo URL"""
        try:
            # This would require bot to be admin in group
            # For now, return default
            
            # Check if we have a cached photo URL
            group_data = json_manager.get_group(group_id)
            if group_data and group_data.get("group_photo"):
                return group_data["group_photo"]
            
            # Return default group image
            return Config.DEFAULT_GROUP
            
        except Exception as e:
            logger.error(f"Error getting group photo: {e}")
            return Config.DEFAULT_GROUP
    
    async def _generate_welcome_voice(self, welcome_data: Dict) -> Optional[str]:
        """Generate welcome voice message"""
        try:
            # Check if voice is enabled
            if not self.wg_config.get("welcome", {}).get("voice", True):
                return None
            
            # Generate voice text
            voice_text = f"""
            আসসালামু আলাইকুম {welcome_data['user']['first_name']}।
            
            {welcome_data['group']['title']} গ্রুপে আপনাকে স্বাগতম।
            
            আপনার যোগদান সময়: {welcome_data['time']['join_time']}
            আজকের দিন: {welcome_data['time']['day_name']}
            
            গ্রুপের নিয়ম মেনে চলুন এবং গ্রুপটি উপভোগ করুন।
            
            ধন্যবাদ।
            """
            
            # Generate voice file
            voice_path = voice_utils.generate_welcome_voice(
                user_name=welcome_data["user"]["first_name"],
                group_name=welcome_data["group"]["title"]
            )
            
            return voice_path
            
        except Exception as e:
            logger.error(f"Error generating welcome voice: {e}")
            return None
    
    def _generate_welcome_buttons(self, user_id: int, chat_id: int):
        """Generate inline buttons for welcome message"""
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Check if inline buttons are enabled
            if not self.wg_config.get("welcome", {}).get("inline_buttons", True):
                return None
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="👤 প্রোফাইল দেখুন",
                        callback_data=f"profile_{user_id}"
                    ),
                    InlineKeyboardButton(
                        text="📜 নিয়ম পড়ুন",
                        callback_data="show_rules"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐ র‍্যাংকিং",
                        callback_data="show_ranking"
                    ),
                    InlineKeyboardButton(
                        text="🆘 সাহায্য",
                        callback_data="help_menu"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📱 মেনু দেখুন",
                        callback_data="main_menu"
                    )
                ]
            ]
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard)
            
        except Exception as e:
            logger.error(f"Error generating welcome buttons: {e}")
            return None
    
    async def _send_welcome_message(self, bot: Bot, chat_id: int, content: Dict):
        """Send welcome message with all content"""
        try:
            # Send image if available
            if content.get("image"):
                await self._send_welcome_image(bot, chat_id, content)
            
            # Send text message with buttons
            await self._send_welcome_text(bot, chat_id, content)
            
            # Send voice if available
            if content.get("voice"):
                await self._send_welcome_voice(bot, chat_id, content)
            
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
    
    async def _send_welcome_image(self, bot: Bot, chat_id: int, content: Dict):
        """Send welcome image"""
        try:
            image_path = content["image"]
            
            if os.path.exists(image_path):
                photo = FSInputFile(image_path)
                
                # Create caption with user info
                caption = self._create_image_caption(content["data"])
                
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption[:1000],  # Telegram caption limit
                    parse_mode="Markdown"
                )
                
                # Clean up temp file after sending
                os.remove(image_path)
                
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
    
    def _create_image_caption(self, data: Dict) -> str:
        """Create caption for welcome image"""
        caption = f"🎉 স্বাগতম {data['user']['full_name']}!\n\n"
        caption += f"📅 যোগ: {data['time']['join_date']}\n"
        caption += f"🆔 আইডি: `{data['user']['id']}`\n"
        caption += f"🏆 র‍্যাংক: {data['user']['rank']}\n"
        caption += f"👥 সিরিয়াল: {data['group']['member_serial']}/{data['group']['member_count']}"
        
        return caption
    
    async def _send_welcome_text(self, bot: Bot, chat_id: int, content: Dict):
        """Send welcome text message"""
        try:
            text = content["text"]
            buttons = content.get("buttons")
            
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=buttons,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome text: {e}")
    
    async def _send_welcome_voice(self, bot: Bot, chat_id: int, content: Dict):
        """Send welcome voice message"""
        try:
            voice_path = content["voice"]
            
            if os.path.exists(voice_path):
                voice = FSInputFile(voice_path)
                
                await bot.send_voice(
                    chat_id=chat_id,
                    voice=voice,
                    caption="🎤 আপনার স্বাগতম বার্তা"
                )
                
                # Clean up temp file after sending
                os.remove(voice_path)
                
        except Exception as e:
            logger.error(f"Error sending welcome voice: {e}")
    
    def _log_welcome_event(self, user_id: int, chat_id: int):
        """Log welcome event"""
        try:
            json_manager.log_action(
                action_type="welcome",
                user_id=user_id,
                details={
                    "chat_id": chat_id,
                    "timestamp": datetime.now().isoformat(),
                    "bot_version": "1.0.0"
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging welcome event: {e}")
    
    # ============ ADMIN FUNCTIONS ============
    
    async def send_custom_welcome(self, bot: Bot, chat_id: int, user_id: int, 
                                custom_message: str = None) -> bool:
        """
        Send custom welcome message (admin function)
        """
        try:
            # Get user info
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return False
            
            # Get chat info
            chat = await bot.get_chat(chat_id)
            
            # Prepare data
            welcome_data = self._prepare_welcome_data(
                user={
                    "id": user_id,
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "language_code": user_data.get("language_code", "en"),
                    "is_bot": False
                },
                chat=chat,
                user_info=user_data,
                group_info=json_manager.get_group(chat_id) or {}
            )
            
            # Generate welcome text
            if custom_message:
                welcome_text = custom_message
            else:
                welcome_text = self._generate_welcome_text(welcome_data)
            
            # Send message
            await bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending custom welcome: {e}")
            return False
    
    async def update_welcome_config(self, config: Dict) -> bool:
        """
        Update welcome configuration (admin function)
        """
        try:
            # Update in-memory config
            if "welcome" in config:
                self.wg_config["welcome"] = {
                    **self.wg_config.get("welcome", {}),
                    **config["welcome"]
                }
            
            # Save to file
            import json
            with open(Config.WG_JSON, 'w', encoding='utf-8') as f:
                json.dump(self.wg_config, f, indent=2, ensure_ascii=False)
            
            logger.info("Welcome configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating welcome config: {e}")
            return False
    
    def get_welcome_stats(self, chat_id: int = None) -> Dict:
        """
        Get welcome statistics
        """
        try:
            stats = {
                "total_welcomes": 0,
                "today_welcomes": 0,
                "top_welcomed_users": [],
                "welcome_settings": self.wg_config.get("welcome", {})
            }
            
            # Get all users
            all_users = json_manager.get_all_users()
            
            # Count welcomes
            for user in all_users:
                join_count = user.get("join_count", 0)
                stats["total_welcomes"] += join_count
                
                # Check if joined today
                join_date = user.get("join_date")
                if join_date:
                    try:
                        join_datetime = datetime.fromisoformat(join_date)
                        if join_datetime.date() == datetime.now().date():
                            stats["today_welcomes"] += 1
                    except:
                        pass
            
            # Get top welcomed users (most active new users)
            active_new_users = []
            for user in all_users:
                messages = user.get("messages_count", 0)
                join_date = user.get("join_date")
                
                if join_date:
                    try:
                        join_datetime = datetime.fromisoformat(join_date)
                        days_in_group = (datetime.now() - join_datetime).days
                        
                        if days_in_group <= 7:  # Joined in last 7 days
                            activity_score = messages / max(days_in_group, 1)
                            active_new_users.append({
                                "user_id": user.get("user_id"),
                                "name": user.get("first_name", "Unknown"),
                                "messages": messages,
                                "join_date": join_date,
                                "activity_score": activity_score
                            })
                    except:
                        pass
            
            # Sort by activity score
            active_new_users.sort(key=lambda x: x["activity_score"], reverse=True)
            stats["top_welcomed_users"] = active_new_users[:5]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting welcome stats: {e}")
            return {}
    
    async def welcome_back_user(self, bot: Bot, user_id: int, chat_id: int):
        """
        Welcome back a returning user
        """
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return False
            
            join_count = user_data.get("join_count", 0)
            
            if join_count > 1:
                # User is returning
                welcome_back_text = f"""
                👋 **ফিরে আসার জন্য ধন্যবাদ {user_data.get('first_name')}!**
                
                এটি আপনার #{join_count}তম বার এই গ্রুপে ফিরে আসা।
                
                আপনার শেষ যোগদান: {user_data.get('last_seen', 'অজানা')}
                মোট মেসেজ: {user_data.get('messages_count', 0)}
                বর্তমান র‍্যাংক: {user_data.get('rank', 'নতুন')}
                
                গ্রুপের একটিভিটি আবার উপভোগ করুন! 🎉
                """
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=welcome_back_text,
                    parse_mode="Markdown"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error welcoming back user: {e}")
            return False
    
    # ============ TESTING AND DEBUGGING ============
    
    async def test_welcome_system(self, bot: Bot, chat_id: int):
        """
        Test the welcome system with a dummy user
        """
        try:
            # Create dummy user data
            dummy_user = {
                "id": 999999999,
                "username": "test_user",
                "first_name": "টেস্ট",
                "last_name": "ইউজার",
                "language_code": "bn",
                "is_bot": False
            }
            
            # Create dummy chat
            dummy_chat = await bot.get_chat(chat_id)
            
            # Simulate welcome
            await self.handle_welcome(bot, type('Event', (), {
                'new_chat_member': type('ChatMember', (), {
                    'user': type('User', (), dummy_user)()
                })(),
                'chat': dummy_chat
            })())
            
            logger.info("Welcome system test completed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing welcome system: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Cleanup temporary welcome files"""
        try:
            import time
            import glob
            
            current_time = time.time()
            temp_dir = Config.TEMP_IMAGES
            
            # Cleanup old welcome images
            pattern = os.path.join(temp_dir, "welcome_*.jpg")
            for filepath in glob.glob(pattern):
                file_time = os.path.getmtime(filepath)
                if current_time - file_time > 3600:  # 1 hour
                    os.remove(filepath)
            
            logger.debug("Cleaned up welcome temp files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
