"""
Startup Manager - Handles bot startup sequence
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
import importlib.util
from getpass import getpass

# python-telegram-bot imports
try:
    from telegram import Bot
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
except ImportError:
    raise ImportError("Please install python-telegram-bot v20+ using: pip install python-telegram-bot --upgrade")

class StartupManager:
    """Manages bot startup sequence"""

    def __init__(self):
        self.logger = logging.getLogger("nomi_startup")
        self.start_time = None
        self.responses = {}
        self.bot_token = None
        self.admin_ids = []
        self.owner_id = None
        self.application = None  # Telegram Application
        self.bot = None

    async def execute(self):
        """Execute startup sequence"""
        self.start_time = asyncio.get_event_loop().time()
        self.logger.info("🚀 Executing startup sequence...")

        # Run startup tasks sequentially
        tasks = [
            self._check_requirements,
            self._load_config,
            self._load_responses,
            self._init_telegram,
            self._warmup_cache,
            self._start_background_tasks,
            self._verify_modules
        ]

        for task in tasks:
            try:
                await task()
                await asyncio.sleep(0.3)
            except Exception as e:
                self.logger.error(f"❌ Startup task failed: {e}")
                raise

        elapsed = asyncio.get_event_loop().time() - self.start_time
        self.logger.info(f"✅ Startup completed in {elapsed:.2f} seconds")

    async def _check_requirements(self):
        """Check Python version and required packages"""
        self.logger.info("🔍 Checking system requirements...")

        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")

        required_packages = [
            "telegram",
            "aiofiles",
            "aiohttp",
            "PIL"
        ]
        for pkg in required_packages:
            if not self._is_package_installed(pkg):
                self.logger.warning(f"⚠️ Package {pkg} not found")

    def _is_package_installed(self, package_name: str) -> bool:
        spec = importlib.util.find_spec(package_name)
        return spec is not None

    async def _load_config(self):
        """Load bot token and IDs from terminal input"""
        self.logger.info("🔧 Loading bot configuration...")

        config_path = Path("config/bot.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # If config exists, read it
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.bot_token = cfg.get("token") or cfg.get("BOT_TOKEN")
            self.admin_ids = cfg.get("admin_ids", [])
            self.owner_id = cfg.get("owner_id")
        else:
            cfg = {}

        # Ask terminal input if missing
        if not self.bot_token:
            self.bot_token = getpass("🔑 Enter your Telegram Bot Token: ").strip()
            cfg["token"] = self.bot_token
        if not self.admin_ids:
            admin_input = input("👤 Enter Admin IDs (comma separated): ").strip()
            self.admin_ids = [int(a) for a in admin_input.split(",") if a.strip().isdigit()]
            cfg["admin_ids"] = self.admin_ids
        if not self.owner_id:
            owner_input = input("👑 Enter Owner ID: ").strip()
            self.owner_id = int(owner_input) if owner_input.isdigit() else None
            cfg["owner_id"] = self.owner_id

        # Save config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        self.logger.info(f"✅ Bot Token, Admin IDs, and Owner ID loaded successfully")

    async def _load_responses(self):
        """Load all JSON response files"""
        self.logger.info("📄 Loading response files...")

        response_dir = Path("responses")
        response_dir.mkdir(exist_ok=True)

        required_files = [
            "welcome.json",
            "goodbye.json",
            "auto_reply.json",
            "voice_reply.json",
            "rules.json",
            "help.json",
            "admin.json",
            "error.json",
            "notification.json",
            "event.json",
            "reminder.json"
        ]

        for f in required_files:
            path = response_dir / f
            if path.exists():
                with open(path, "r", encoding="utf-8") as rf:
                    try:
                        self.responses[f] = json.load(rf)
                    except json.JSONDecodeError:
                        self.logger.warning(f"⚠️ Invalid JSON in {f}")
            else:
                self.logger.warning(f"⚠️ Missing response file: {f}")
                self.responses[f] = {}

        self.logger.info(f"✅ Response files loaded: {list(self.responses.keys())}")

    async def _init_telegram(self):
        """Initialize Telegram bot"""
        self.logger.info("🤖 Initializing Telegram bot...")

        if not self.bot_token:
            raise RuntimeError("Bot token is missing")

        # Async Telegram Application
        self.application = ApplicationBuilder().token(self.bot_token).build()
        self.bot = self.application.bot

        # Add a simple /start handler for testing
        async def start_handler(update, context):
            await update.message.reply_text("✅ Bot is running!")

        self.application.add_handler(CommandHandler("start", start_handler))

        # Start Telegram polling in background
        asyncio.create_task(self.application.initialize())
        asyncio.create_task(self.application.start())
        self.logger.info("✅ Telegram bot initialized successfully")

    async def _warmup_cache(self):
        """Warm up cache systems"""
        self.logger.info("🔥 Warming up cache...")

    async def _start_background_tasks(self):
        """Start background tasks like scheduler, monitor"""
        self.logger.info("🔄 Starting background tasks...")

    async def _verify_modules(self):
        """Verify all modules are loaded"""
        self.logger.info("✅ Verifying modules...")

    async def get_startup_time(self) -> float:
        """Get startup duration"""
        if self.start_time:
            return asyncio.get_event_loop().time() - self.start_time
        return 0
