"""
Updated config with inline button settings
"""

import os
from typing import Dict, List, Any

class Config:
    # Bot Token (Replace with your bot token)
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    # Admin IDs
    ADMIN_IDS = [123456789, 987654321]  # Replace with actual admin IDs
    
    # Bot Settings
    BOT_USERNAME = None
    BOT_ID = None
    BOT_NAME = "𝗬𝗢𝗨𝗥 𝗖𝗥𝗨𝗦𝗛"
    
    # Inline Button Settings
    INVITE_LINK = "https://t.me/{bot_username}?startgroup=true"
    SUPPORT_CHAT = "https://t.me/your_support_chat"
    UPDATE_CHANNEL = "https://t.me/your_update_channel"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Database paths
    DB_USERS = os.path.join(BASE_DIR, "db/users.json")
    DB_GROUPS = os.path.join(BASE_DIR, "db/groups.json")
    DB_SYSTEM = os.path.join(BASE_DIR, "db/system.json")
    DB_LOGS = os.path.join(BASE_DIR, "db/logs.json")
    
    # JSON Config paths
    WG_JSON = os.path.join(BASE_DIR, "wg.json")
    DEFAULT_JSON = os.path.join(BASE_DIR, "default.json")
    
    # Assets paths
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    
    # Image paths
    BG_IMAGE = os.path.join(ASSETS_DIR, "bg.jpg")
    FONT_FILE = os.path.join(ASSETS_DIR, "font.ttf")
    DEFAULT_PROFILE = os.path.join(ASSETS_DIR, "default_profile.png")
    DEFAULT_GROUP = os.path.join(ASSETS_DIR, "default_group.png")
    
    # Temp paths
    TEMP_IMAGES = os.path.join(TEMP_DIR, "images")
    TEMP_VOICE = os.path.join(TEMP_DIR, "voice")
    
    # Moderation settings
    MAX_MESSAGES_PER_MINUTE = 10
    SPAM_DETECTION_THRESHOLD = 5
    FLOOD_WINDOW_SECONDS = 5
    MAX_WARNINGS = 3
    
    # Welcome settings
    WELCOME_ENABLED = True
    GOODBYE_ENABLED = True
    AUTO_REPLY_ENABLED = True
    
    # Voice settings
    VOICE_ENABLED = True
    VOICE_LANG = "bn"  # Bangla
    
    # Security settings
    ANTI_SPAM = True
    ANTI_FLOOD = True
    ANTI_LINKS = True
    ANTI_BAD_WORDS = True
    
    # User system
    ENABLE_RANKS = True
    ENABLE_BADGES = True
    ENABLE_REPUTATION = True
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.TEMP_IMAGES,
            cls.TEMP_VOICE,
            os.path.join(cls.BASE_DIR, "db"),
            cls.ASSETS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def init_bot_info(cls, bot):
        """Initialize bot information"""
        cls.BOT_USERNAME = bot.username
        cls.BOT_ID = bot.id
        cls.INVITE_LINK = f"https://t.me/{bot.username}?startgroup=true"

# Create directories on import
Config.create_directories()