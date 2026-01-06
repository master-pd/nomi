"""
Main file with inline button support
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION

from config import Config
from utils.logger_utils import setup_logger
from utils.json_utils import JSONManager
from features.welcome import WelcomeSystem
from features.goodbye import GoodbyeSystem
from features.auto_reply import AutoReplySystem
from features.moderation import ModerationSystem
from features.logging import LoggingSystem
from features.inline_buttons import InlineButtonSystem, GroupStates

# Setup logging
logger = setup_logger("your_crush_bot")

# Initialize systems
json_manager = JSONManager()
welcome_system = WelcomeSystem()
goodbye_system = GoodbyeSystem()
auto_reply = AutoReplySystem()
moderation = ModerationSystem()
logging_system = LoggingSystem()

# Initialize bot and dispatcher
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()

# Initialize inline button system
inline_system = InlineButtonSystem(bot)

class YourCrushBot:
    def __init__(self):
        self.bot = bot
        self.dp = dp
        self.started_at = datetime.now()
        self.inline_system = inline_system
        
    async def setup_bot(self):
        """Setup bot information"""
        bot_info = await self.bot.get_me()
        Config.init_bot_info(bot_info)
        logger.info(f"🤖 Bot Started: @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"📅 Started at: {self.started_at}")
        logger.info("✅ Bot is ready to serve!")
    
    def register_handlers(self):
        """Register all handlers"""
        
        # Command handlers
        @self.dp.message(Command("start"))
        async def start_command(message: Message):
            await self.handle_start(message)
        
        @self.dp.message(Command("menu"))
        async def menu_command(message: Message):
            await self.show_inline_menu(message)
        
        @self.dp.message(Command("help"))
        async def help_command(message: Message):
            await self.handle_help(message)
        
        @self.dp.message(Command("profile"))
        async def profile_command(message: Message):
            await self.handle_profile(message)
        
        @self.dp.message(Command("rank"))
        async def rank_command(message: Message):
            await self.handle_rank(message)
        
        @self.dp.message(Command("rules"))
        async def rules_command(message: Message):
            await self.handle_rules(message)
        
        @self.dp.message(Command("stats"))
        async def stats_command(message: Message):
            await self.handle_stats(message)
        
        @self.dp.message(Command("invite"))
        async def invite_command(message: Message):
            await self.show_invite_menu(message)
        
        # Callback query handler
        @self.dp.callback_query()
        async def callback_handler(callback_query: CallbackQuery):
            await self.inline_system.handle_callback_query(callback_query)
        
        # Welcome handler
        @self.dp.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
        async def on_user_join(event: ChatMemberUpdated):
            await self.handle_welcome(event)
        
        # Goodbye handler
        @self.dp.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
        async def on_user_leave(event: ChatMemberUpdated):
            await self.handle_goodbye(event)
        
        # Message handler
        @self.dp.message()
        async def on_message(message: Message):
            await self.handle_message(message)
    
    async def handle_start(self, message: Message):
        """Handle /start command with inline menu"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Update user data
        user_data = {
            "user_id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "started_bot": True,
            "start_date": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "language_code": message.from_user.language_code or "en"
        }
        
        json_manager.update_user(user_id, user_data)
        
        # Check if start parameter has group info
        if len(message.text.split()) > 1:
            start_param = message.text.split()[1]
            if start_param.startswith("group"):
                # Handle group start parameter
                await self.handle_group_start(message, start_param)
                return
        
        welcome_text = f"""
        🎉 **আসসালামু আলাইকুম {message.from_user.first_name}!**
        
        আমি **{Config.BOT_NAME}** - একটি প্রফেশনাল টেলিগ্রাম বট।
        
        ✨ **ফিচারসমূহ:**
        • অটো ওয়েলকাম মেসেজ 📸
        • ইন্টেলিজেন্ট মডারেশন 🛡️
        • ইউজার র‍্যাংকিং & ব্যাজ 🏆
        • বাংলা ভয়েস রিপ্লাই 🔊
        • ইনলাইন গ্রুপ কন্ট্রোল 📋
        
        📌 **বটটিকে গ্রুপে অ্যাড করতে নিচের মেনু ব্যবহার করুন।**
        """
        
        await message.answer(
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    async def handle_group_start(self, message: Message, start_param: str):
        """Handle group start parameter"""
        group_info = start_param.split("_")
        
        if len(group_info) > 1:
            group_id = group_info[1]
            # You can add specific group handling logic here
            pass
        
        await message.answer(
            text="✅ বটটিকে গ্রুপে অ্যাড করার জন্য ধন্যবাদ!\n\n"
                 "এখন আপনি গ্রুপ ম্যানেজমেন্ট মেনু ব্যবহার করতে পারেন।",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    async def show_inline_menu(self, message: Message):
        """Show inline menu"""
        menu_text = f"""
        📱 **{Config.BOT_NAME} - ইনলাইন মেনু**
        
        বট কন্ট্রোল এবং গ্রুপ ম্যানেজমেন্টের জন্য নিচের অপশনগুলো ব্যবহার করুন।
        
        **কুইক একশন:**
        📋 গ্রুপ লিস্ট দেখুন
        ➕ নতুন গ্রুপে অ্যাড করুন
        ⚙️ বট সেটিংস
        🆘 সাহায্য
        """
        
        await message.answer(
            text=menu_text,
            parse_mode="Markdown",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    async def show_invite_menu(self, message: Message):
        """Show invite menu"""
        invite_text = f"""
        📨 **ইনভাইটেশন লিংক**
        
        বটটিকে আপনার গ্রুপে অ্যাড করতে নিচের লিংক ব্যবহার করুন:
        
        **সাধারণ ইনভাইট লিংক:**
        `https://t.me/{Config.BOT_USERNAME}?startgroup=true`
        
        **এডমিন পারমিশন সহ:**
        `https://t.me/{Config.BOT_USERNAME}?startgroup=true&admin=post_messages+delete_messages+restrict_members+invite_users`
        
        অথবা নিচের বাটনে ক্লিক করুন:
        """
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ গ্রুপে অ্যাড করুন",
                        url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👑 এডমিন পারমিশন সহ",
                        url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true&admin=post_messages+delete_messages+restrict_members+invite_users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 গ্রুপ লিস্ট",
                        callback_data="group_list"
                    )
                ]
            ]
        )
        
        await message.answer(
            text=invite_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def handle_welcome(self, event: ChatMemberUpdated):
        """Handle new member join"""
        if Config.WELCOME_ENABLED:
            await welcome_system.handle_welcome(self.bot, event)
            
            # Update group data
            group_id = event.chat.id
            group_data = {
                "id": group_id,
                "title": event.chat.title,
                "member_count": await event.chat.get_member_count(),
                "last_activity": datetime.now().isoformat(),
                "welcome_count": json_manager.get_group_stat(group_id, "welcome_count", 0) + 1
            }
            json_manager.update_group(group_id, group_data)
    
    async def handle_goodbye(self, event: ChatMemberUpdated):
        """Handle member leave"""
        if Config.GOODBYE_ENABLED:
            await goodbye_system.handle_goodbye(self.bot, event)
    
    async def handle_message(self, message: Message):
        """Handle all messages"""
        
        # Skip bot's own messages
        if message.from_user.id == Config.BOT_ID:
            return
        
        # Check if message is from a group
        if message.chat.type in ["group", "supergroup"]:
            # Update group data
            group_id = message.chat.id
            group_data = {
                "id": group_id,
                "title": message.chat.title,
                "member_count": await message.chat.get_member_count(),
                "last_activity": datetime.now().isoformat(),
                "total_messages": json_manager.get_group_stat(group_id, "total_messages", 0) + 1
            }
            json_manager.update_group(group_id, group_data)
            
            # Apply moderation
            moderation_result = await moderation.check_message(message)
            
            if moderation_result.get("action_required"):
                action = moderation_result.get("action")
                if action == "delete":
                    await message.delete()
                elif action == "warn":
                    await message.answer(f"⚠️ {message.from_user.first_name}, নিয়ম ভঙ্গ করবেন না!")
            
            # Log message for analytics
            logging_system.log_message(message)
            
            # Update user stats
            json_manager.increment_user_stat(
                message.from_user.id,
                "messages_count"
            )
        
        # Auto reply system
        if Config.AUTO_REPLY_ENABLED:
            reply = await auto_reply.get_reply(message.text)
            if reply:
                await message.answer(reply)
                
                # Send voice if enabled
                if Config.VOICE_ENABLED:
                    voice_path = await auto_reply.generate_voice(reply)
                    if voice_path:
                        await message.answer_voice(types.FSInputFile(voice_path))
    
    async def handle_help(self, message: Message):
        """Handle /help command"""
        help_text = f"""
        🤖 **{Config.BOT_NAME} - সাহায্য কেন্দ্র**
        
        📋 **মূল কমান্ড:**
        /start - বট শুরু করুন
        /menu - ইনলাইন মেনু দেখুন
        /help - সাহায্য দেখুন
        /invite - ইনভাইট লিংক পান
        
        📊 **ইউজার কমান্ড:**
        /profile - আপনার প্রোফাইল
        /rank - র‍্যাংক দেখুন
        /stats - গ্রুপ পরিসংখ্যান
        /rules - গ্রুপের নিয়ম
        
        ⚙️ **গ্রুপ ম্যানেজমেন্ট:**
        • ইনলাইন বাটন ব্যবহার করে গ্রুপ সিলেক্ট করুন
        • গ্রুপ লিস্ট থেকে কোনো গ্রুপ বাছাই করুন
        • স্পেসিফিক গ্রুপে বট ইনভাইট করুন
        
        🔗 **লিংকসমূহ:**
        📢 আপডেট চ্যানেল: {Config.UPDATE_CHANNEL}
        👥 সাপোর্ট গ্রুপ: {Config.SUPPORT_CHAT}
        
        নিচের মেনু বাটনে ক্লিক করে সম্পূর্ণ ফিচার এক্সেস করুন:
        """
        
        await message.answer(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    async def handle_profile(self, message: Message):
        """Handle /profile command"""
        user_id = message.from_user.id
        user_data = json_manager.get_user(user_id)
        
        if not user_data:
            await message.answer("❌ আপনার তথ্য ডাটাবেসে নেই।")
            return
        
        # Create profile with inline buttons
        profile_text = f"""
        👤 **প্রোফাইল:** {user_data.get('first_name', 'Unknown')}
        
        🆔 **ইউজার আইডি:** `{user_id}`
        📱 **ইউজারনেম:** @{user_data.get('username', 'N/A')}
        🏆 **র‍্যাংক:** {user_data.get('rank', 'নতুন')}
        ⭐ **রিপুটেশন:** {user_data.get('reputation', 0)}
        💬 **মেসেজ:** {user_data.get('messages_count', 0)}
        📅 **যোগদান:** {user_data.get('join_date', 'N/A')[:10]}
        🌐 **ভাষা:** {user_data.get('language_code', 'en')}
        """
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 বিস্তারিত স্ট্যাটস",
                        callback_data=f"user_stats_{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏆 ব্যাজ দেখুন",
                        callback_data=f"user_badges_{user_id}"
                    ),
                    InlineKeyboardButton(
                        text="📈 র‍্যাংকিং",
                        callback_data="user_ranking"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 মেনুতে ফিরুন",
                        callback_data="back_to_menu"
                    )
                ]
            ]
        )
        
        await message.answer(
            text=profile_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def handle_rank(self, message: Message):
        """Handle /rank command"""
        user_id = message.from_user.id
        user_data = json_manager.get_user(user_id)
        
        if not user_data:
            await message.answer("❌ আপনার তথ্য ডাটাবেসে নেই।")
            return
        
        # Calculate rank based on messages
        messages = user_data.get('messages_count', 0)
        
        if messages >= 1000:
            rank = "👑 কিং"
            level = 10
        elif messages >= 500:
            rank = "⭐ স্টার"
            level = 9
        elif messages >= 250:
            rank = "🔥 ফায়ার"
            level = 8
        elif messages >= 100:
            rank = "💎 ডায়মন্ড"
            level = 7
        elif messages >= 50:
            rank = "🏅 গোল্ড"
            level = 6
        elif messages >= 25:
            rank = "🥈 সিলভার"
            level = 5
        elif messages >= 10:
            rank = "🥉 ব্রোঞ্জ"
            level = 4
        elif messages >= 5:
            rank = "📊 একটিভ"
            level = 3
        elif messages >= 1:
            rank = "👤 মেম্বার"
            level = 2
        else:
            rank = "🆕 নিউ"
            level = 1
        
        # Update user rank
        user_data['rank'] = rank
        user_data['level'] = level
        json_manager.update_user(user_id, user_data)
        
        rank_text = f"""
        🏆 **র‍্যাংক তথ্য**
        
        **ইউজার:** {user_data.get('first_name', 'Unknown')}
        **বর্তমান র‍্যাংক:** {rank}
        **লেভেল:** {level}
        **মেসেজ সংখ্যা:** {messages}
        **রিপুটেশন:** {user_data.get('reputation', 0)}
        
        **পরবর্তী র‍্যাংক:**
        {self.get_next_rank_info(messages, rank)}
        
        **র‍্যাংক সিস্টেম:**
        • 1-4 মেসেজ: নিউ
        • 5-9 মেসেজ: মেম্বার
        • 10-24 মেসেজ: একটিভ
        • 25-49 মেসেজ: ব্রোঞ্জ
        • 50-99 মেসেজ: সিলভার
        • 100-249 মেসেজ: গোল্ড
        • 250-499 মেসেজ: ডায়মন্ড
        • 500-999 মেসেজ: ফায়ার
        • 1000+ মেসেজ: কিং
        """
        
        await message.answer(
            text=rank_text,
            parse_mode="Markdown",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    def get_next_rank_info(self, current_messages: int, current_rank: str) -> str:
        """Get next rank information"""
        rank_thresholds = {
            "🆕 নিউ": (5, "👤 মেম্বার"),
            "👤 মেম্বার": (10, "📊 একটিভ"),
            "📊 একটিভ": (25, "🥉 ব্রোঞ্জ"),
            "🥉 ব্রোঞ্জ": (50, "🥈 সিলভার"),
            "🥈 সিলভার": (100, "🏅 গোল্ড"),
            "🏅 গোল্ড": (250, "💎 ডায়মন্ড"),
            "💎 ডায়মন্ড": (500, "🔥 ফায়ার"),
            "🔥 ফায়ার": (1000, "👑 কিং"),
            "👑 কিং": (float('inf'), "শীর্ষস্থান")
        }
        
        if current_rank in rank_thresholds:
            needed, next_rank = rank_thresholds[current_rank]
            remaining = max(0, needed - current_messages)
            
            if remaining > 0:
                return f"{remaining} মেসেজ বাকি {next_rank} র‍্যাংক পেতে"
            else:
                return f"আপনি ইতিমধ্যে সর্বোচ্চ র‍্যাংক এ আছেন!"
        else:
            return "র‍্যাংক সিস্টেম আপডেট হচ্ছে"
    
    async def handle_rules(self, message: Message):
        """Handle /rules command"""
        rules_text = """
        📜 **গ্রুপের নিয়মাবলী**
        
        1. **সবার সাথে সম্মানজনক আচরণ করুন**
        2. **স্প্যাম করবেন না**
        3. **অনুপযুক্ত কন্টেন্ট শেয়ার করবেন না**
        4. **ব্যক্তিগত আক্রমণ করবেন না**
        5. **বটকে অপব্যবহার করবেন না**
        
        **নিয়ম ভঙ্গের ফলাফল:**
        • প্রথমবার: সতর্কতা
        • দ্বিতীয়বার: 1 ঘন্টা মিউট
        • তৃতীয়বার: 1 দিন মিউট
        • চতুর্থবার: স্থায়ী ব্যান
        
        **বট পারমিশন:**
        ✅ মেসেজ ডিলিট করা
        ✅ ইউজার মিউট করা
        ✅ লিংক ডিটেক্ট করা
        ✅ স্প্যাম ডিটেক্ট করা
        """
        
        await message.answer(
            text=rules_text,
            parse_mode="Markdown",
            reply_markup=self.inline_system.create_main_menu()
        )
    
    async def handle_stats(self, message: Message):
        """Handle /stats command"""
        all_users = json_manager.get_all_users()
        all_groups = json_manager.get_all_groups()
        
        total_users = len(all_users)
        total_groups = len(all_groups)
        total_messages = sum(user.get('messages_count', 0) for user in all_users)
        
        # Top 5 active users
        top_users = sorted(all_users, key=lambda x: x.get('messages_count', 0), reverse=True)[:5]
        
        stats_text = f"""
        📊 **সিস্টেম পরিসংখ্যান**
        
        **সারাংশ:**
        👥 মোট ইউজার: {total_users}
        📋 মোট গ্রুপ: {total_groups}
        💬 মোট মেসেজ: {total_messages}
        
        **টপ ৫ একটিভ ইউজার:**
        """
        
        for i, user in enumerate(top_users, start=1):
            stats_text += f"\n{i}. {user.get('first_name', 'Unknown')} - {user.get('messages_count', 0)} মেসেজ"
        
        stats_text += f"\n\n**টপ ৩ একটিভ গ্রুপ:**"
        
        top_groups = sorted(all_groups, key=lambda x: x.get('total_messages', 0), reverse=True)[:3]
        for i, group in enumerate(top_groups, start=1):
            stats_text += f"\n{i}. {group.get('title', 'Unknown')} - {group.get('total_messages', 0)} মেসেজ"
        
        stats_text += "\n\nনিচের বাটন থেকে বিস্তারিত দেখুন:"
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📈 ডিটেইলড স্ট্যাটস",
                        callback_data="detailed_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 গ্রুপ লিস্ট",
                        callback_data="group_list"
                    ),
                    InlineKeyboardButton(
                        text="👥 ইউজার লিস্ট",
                        callback_data="user_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 মেনুতে ফিরুন",
                        callback_data="back_to_menu"
                    )
                ]
            ]
        )
        
        await message.answer(
            text=stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    async def run(self):
        """Run the bot"""
        await self.setup_bot()
        self.register_handlers()
        
        logger.info("🔄 Polling started...")
        await self.dp.start_polling(self.bot)

# Run the bot
async def main():
    bot_instance = YourCrushBot()
    await bot_instance.run()

if __name__ == "__main__":
    asyncio.run(main())