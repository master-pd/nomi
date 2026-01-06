"""
Inline Button System for Your Crush Bot
With Group Selection and Invite Features
"""

import logging
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    WebAppInfo
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import Config
from utils.json_utils import JSONManager

logger = logging.getLogger(__name__)
json_manager = JSONManager()

class GroupStates(StatesGroup):
    """States for group selection"""
    SELECTING_GROUP = State()
    CONFIRMING_INVITE = State()

class InlineButtonSystem:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.json_manager = JSONManager()
    
    def create_main_menu(self) -> InlineKeyboardMarkup:
        """
        Create main menu with inline buttons
        """
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ আমাকে গ্রুপে অ্যাড করুন",
                        url=Config.INVITE_LINK
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 গ্রুপ লিস্ট",
                        callback_data="group_list"
                    ),
                    InlineKeyboardButton(
                        text="🏆 টপ গ্রুপ",
                        callback_data="top_groups"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 সাপোর্ট গ্রুপ",
                        url=Config.SUPPORT_CHAT
                    ),
                    InlineKeyboardButton(
                        text="📢 আপডেট চ্যানেল",
                        url=Config.UPDATE_CHANNEL
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ বট সেটিংস",
                        callback_data="bot_settings"
                    ),
                    InlineKeyboardButton(
                        text="🆘 সাহায্য",
                        callback_data="help_menu"
                    )
                ]
            ]
        )
        return keyboard
    
    def create_group_selection_menu(self, groups: List[Dict], page: int = 0) -> InlineKeyboardMarkup:
        """
        Create paginated group selection menu
        """
        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_groups = groups[start_idx:end_idx]
        
        keyboard_buttons = []
        
        for group in page_groups:
            group_title = group.get('title', 'Unknown Group')
            group_id = group.get('id')
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📊 {group_title}",
                    callback_data=f"select_group_{group_id}"
                )
            ])
        
        # Navigation buttons
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ পূর্বের",
                    callback_data=f"groups_page_{page-1}"
                )
            )
        
        if end_idx < len(groups):
            nav_buttons.append(
                InlineKeyboardButton(
                    text="পরের ▶️",
                    callback_data=f"groups_page_{page+1}"
                )
            )
        
        if nav_buttons:
            keyboard_buttons.append(nav_buttons)
        
        # Back button
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="🔙 মেনুতে ফিরুন",
                callback_data="back_to_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    def create_group_invite_menu(self, group_id: int) -> InlineKeyboardMarkup:
        """
        Create menu for inviting bot to a specific group
        """
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ এই গ্রুপে ইনভাইট করুন",
                        url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true&admin=post_messages+delete_messages+restrict_members+invite_users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 গ্রুপ তথ্য",
                        callback_data=f"group_info_{group_id}"
                    ),
                    InlineKeyboardButton(
                        text="👥 মেম্বার লিস্ট",
                        callback_data=f"group_members_{group_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 গ্রুপ লিস্ট",
                        callback_data="back_to_groups"
                    )
                ]
            ]
        )
        return keyboard
    
    def create_admin_panel(self, user_id: int) -> InlineKeyboardMarkup:
        """
        Create admin panel with special features
        """
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 ড্যাশবোর্ড",
                        callback_data="admin_dashboard"
                    ),
                    InlineKeyboardButton(
                        text="⚙️ কনফিগার",
                        callback_data="admin_config"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 ব্রডকাস্ট",
                        callback_data="admin_broadcast"
                    ),
                    InlineKeyboardButton(
                        text="📈 অ্যানালিটিক্স",
                        callback_data="admin_analytics"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔧 বট কন্ট্রোল",
                        callback_data="admin_control"
                    ),
                    InlineKeyboardButton(
                        text="🔄 আপডেট",
                        callback_data="admin_update"
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
        return keyboard
    
    async def handle_callback_query(self, callback_query: CallbackQuery):
        """
        Handle all callback queries
        """
        data = callback_query.data
        
        if data == "group_list":
            await self.show_group_list(callback_query)
        
        elif data.startswith("groups_page_"):
            page = int(data.split("_")[2])
            await self.show_group_list(callback_query, page)
        
        elif data.startswith("select_group_"):
            group_id = int(data.split("_")[2])
            await self.show_group_invite(callback_query, group_id)
        
        elif data == "top_groups":
            await self.show_top_groups(callback_query)
        
        elif data == "bot_settings":
            await self.show_bot_settings(callback_query)
        
        elif data == "help_menu":
            await self.show_help_menu(callback_query)
        
        elif data == "back_to_menu":
            await self.show_main_menu(callback_query)
        
        elif data == "back_to_groups":
            await self.show_group_list(callback_query)
        
        elif data.startswith("group_info_"):
            group_id = int(data.split("_")[2])
            await self.show_group_info(callback_query, group_id)
        
        elif callback_query.from_user.id in Config.ADMIN_IDS:
            if data == "admin_dashboard":
                await self.show_admin_dashboard(callback_query)
        
        await callback_query.answer()
    
    async def show_main_menu(self, callback_query: CallbackQuery):
        """
        Show main menu
        """
        menu_text = f"""
        🤖 **{Config.BOT_NAME} - মেনু**
        
        বটটিকে আপনার গ্রুপে অ্যাড করে সম্পূর্ণ অটোমেশন পেতে পারেন।
        
        **ফিচারসমূহ:**
        ✅ অটো ওয়েলকাম মেসেজ
        ✅ গ্রুপ মডারেশন
        ✅ ইউজার র‍্যাংকিং
        ✅ ভয়েস রিপ্লাই
        ✅ ইনলাইন কন্ট্রোল
        
        নিচের বাটনগুলো ব্যবহার করুন:
        """
        
        await callback_query.message.edit_text(
            text=menu_text,
            parse_mode="Markdown",
            reply_markup=self.create_main_menu()
        )
    
    async def show_group_list(self, callback_query: CallbackQuery, page: int = 0):
        """
        Show list of groups where bot is added
        """
        groups = self.json_manager.get_all_groups()
        
        if not groups:
            await callback_query.message.edit_text(
                text="📭 বটটি এখনো কোনো গ্রুপে অ্যাড করা হয়নি।\n\n"
                     "প্রথমে বটটিকে একটি গ্রুপে অ্যাড করুন।",
                reply_markup=self.create_main_menu()
            )
            return
        
        total_groups = len(groups)
        start_idx = page * 5 + 1
        
        groups_text = f"""
        📋 **গ্রুপ লিস্ট** (পৃষ্ঠা {page + 1})
        
        মোট গ্রুপ: {total_groups}
        
        **লিস্ট:**
        """
        
        for i, group in enumerate(groups[page*5:(page+1)*5], start=start_idx):
            group_title = group.get('title', 'Unknown Group')
            member_count = group.get('member_count', 0)
            
            groups_text += f"\n{i}. **{group_title}**\n"
            groups_text += f"   👥 সদস্য: {member_count}\n"
            groups_text += f"   📅 যোগ: {group.get('added_date', 'N/A')[:10]}\n"
        
        await callback_query.message.edit_text(
            text=groups_text,
            parse_mode="Markdown",
            reply_markup=self.create_group_selection_menu(groups, page)
        )
    
    async def show_group_invite(self, callback_query: CallbackQuery, group_id: int):
        """
        Show invite button for specific group
        """
        group = self.json_manager.get_group(group_id)
        
        if not group:
            await callback_query.answer("❌ গ্রুপটি পাওয়া যায়নি!", show_alert=True)
            return
        
        group_title = group.get('title', 'Unknown Group')
        member_count = group.get('member_count', 0)
        
        invite_text = f"""
        📨 **গ্রুপ ইনভাইটেশন**
        
        **গ্রুপ:** {group_title}
        **সদস্য সংখ্যা:** {member_count}
        **গ্রুপ আইডি:** `{group_id}`
        
        নিচের বাটনে ক্লিক করে এই গ্রুপে বটটিকে অ্যাড করুন।
        
        **প্রয়োজনীয় পারমিশন:**
        ✅ মেসেজ পোস্ট করা
        ✅ মেসেজ ডিলিট করা
        ✅ মেম্বার রেস্ট্রিক্ট করা
        ✅ ইউজার ইনভাইট করা
        """
        
        await callback_query.message.edit_text(
            text=invite_text,
            parse_mode="Markdown",
            reply_markup=self.create_group_invite_menu(group_id)
        )
    
    async def show_top_groups(self, callback_query: CallbackQuery):
        """
        Show top groups by activity
        """
        groups = self.json_manager.get_all_groups()
        
        # Sort by member count
        sorted_groups = sorted(groups, key=lambda x: x.get('member_count', 0), reverse=True)
        
        top_text = "🏆 **টপ একটিভ গ্রুপসমূহ**\n\n"
        
        for i, group in enumerate(sorted_groups[:10], start=1):
            group_title = group.get('title', 'Unknown Group')
            member_count = group.get('member_count', 0)
            message_count = group.get('total_messages', 0)
            
            top_text += f"{i}. **{group_title}**\n"
            top_text += f"   👥 {member_count} সদস্য | 💬 {message_count} মেসেজ\n"
        
        await callback_query.message.edit_text(
            text=top_text,
            parse_mode="Markdown",
            reply_markup=self.create_main_menu()
        )
    
    async def show_bot_settings(self, callback_query: CallbackQuery):
        """
        Show bot settings
        """
        settings_text = f"""
        ⚙️ **বট সেটিংস**
        
        **বট তথ্য:**
        🤖 নাম: {Config.BOT_NAME}
        📱 ইউজারনেম: @{Config.BOT_USERNAME}
        🆔 আইডি: {Config.BOT_ID}
        
        **সক্রিয় ফিচার:**
        ✅ Welcome System: {Config.WELCOME_ENABLED}
        ✅ Goodbye System: {Config.GOODBYE_ENABLED}
        ✅ Auto Reply: {Config.AUTO_REPLY_ENABLED}
        ✅ Voice Support: {Config.VOICE_ENABLED}
        ✅ Moderation: {Config.ANTI_SPAM}
        
        **স্ট্যাটাস:**
        📊 মোট গ্রুপ: {len(self.json_manager.get_all_groups())}
        👥 মোট ইউজার: {len(self.json_manager.get_all_users())}
        """
        
        await callback_query.message.edit_text(
            text=settings_text,
            parse_mode="Markdown",
            reply_markup=self.create_main_menu()
        )
    
    async def show_help_menu(self, callback_query: CallbackQuery):
        """
        Show help menu
        """
        help_text = """
        🆘 **সাহায্য মেনু**
        
        **কমান্ডসমূহ:**
        /start - বট শুরু করুন
        /help - সাহায্য দেখুন
        /profile - প্রোফাইল দেখুন
        /rank - র‍্যাংক দেখুন
        /settings - সেটিংস
        
        **গ্রুপ ইনভাইটেশন:**
        1. "আমাকে গ্রুপে অ্যাড করুন" বাটনে ক্লিক করুন
        2. গ্রুপ সিলেক্ট করুন
        3. পারমিশন দিন এবং অ্যাড করুন
        
        **সাপোর্ট:**
        কোনো সমস্যা হলে সাপোর্ট গ্রুপে যোগাযোগ করুন।
        """
        
        await callback_query.message.edit_text(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=self.create_main_menu()
        )
    
    async def show_group_info(self, callback_query: CallbackQuery, group_id: int):
        """
        Show detailed group information
        """
        group = self.json_manager.get_group(group_id)
        
        if not group:
            await callback_query.answer("❌ গ্রুপটি পাওয়া যায়নি!", show_alert=True)
            return
        
        info_text = f"""
        📊 **গ্রুপ তথ্য**
        
        **নাম:** {group.get('title', 'Unknown')}
        **আইডি:** `{group_id}`
        **সদস্য:** {group.get('member_count', 0)}
        **মেসেজ:** {group.get('total_messages', 0)}
        **যোগদান তারিখ:** {group.get('added_date', 'N/A')}
        **শেষ একটিভিটি:** {group.get('last_activity', 'N/A')}
        
        **সেটিংস:**
        • Welcome: {'✅' if group.get('welcome_enabled', True) else '❌'}
        • Moderation: {'✅' if group.get('moderation_enabled', True) else '❌'}
        • Voice Reply: {'✅' if group.get('voice_enabled', True) else '❌'}
        
        **এডমিনসমূহ:** {len(group.get('admins', []))}
        """
        
        await callback_query.message.edit_text(
            text=info_text,
            parse_mode="Markdown",
            reply_markup=self.create_group_invite_menu(group_id)
        )
    
    async def show_admin_dashboard(self, callback_query: CallbackQuery):
        """
        Show admin dashboard
        """
        dashboard_text = """
        📊 **এডমিন ড্যাশবোর্ড**
        
        **সিস্টেম স্ট্যাটাস:**
        ✅ বট অনলাইন
        ✅ ডাটাবেস সংযুক্ত
        ✅ লগিং সক্রিয়
        
        **কুইক একশন:**
        • ব্রডকাস্ট মেসেজ
        • সিস্টেম আপডেট
        • ব্যাকআপ নিন
        • লগ ক্লিয়ার করুন
        
        নিচের বাটনগুলো ব্যবহার করুন:
        """
        
        await callback_query.message.edit_text(
            text=dashboard_text,
            parse_mode="Markdown",
            reply_markup=self.create_admin_panel(callback_query.from_user.id)
        )