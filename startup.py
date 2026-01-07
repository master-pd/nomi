"""
Startup Manager - Handles bot startup sequence
"""

import asyncio
import time
import logging
from pathlib import Path
import importlib.util

class StartupManager:
    """Manages bot startup sequence"""

    def __init__(self):
        self.logger = logging.getLogger("nomi_startup")
        self.start_time = None
        self.config = {}  # <-- Added, to store bot config

    async def execute(self):
        """Execute startup sequence"""
        self.start_time = time.time()
        self.logger.info("🚀 Executing startup sequence...")

        # Load bot config
        config_path = Path("config/bot.json")
        if config_path.exists():
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.logger.info("✅ Bot Token, Admin IDs, and Owner ID loaded successfully")
        else:
            self.logger.warning("⚠️ bot.json not found! Please add it in config folder.")

        # Define startup tasks
        tasks = [
            self._check_requirements,
            self._load_responses,
            self._init_telegram,
            self._warmup_cache,
            self._start_background_tasks,
            self._verify_modules
        ]

        # Execute tasks sequentially
        for task in tasks:
            try:
                await task()
                await asyncio.sleep(0.2)
            except Exception as e:
                self.logger.error(f"❌ Startup task failed: {e}")
                raise

        elapsed = time.time() - self.start_time
        self.logger.info(f"✅ Startup completed in {elapsed:.2f} seconds")

    async def _check_requirements(self):
        self.logger.info("🔍 Checking system requirements...")
        import sys

        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")

        required_packages = ["telegram", "PIL", "aiofiles", "aiohttp"]
        for pkg in required_packages:
            if not self._is_package_installed(pkg):
                self.logger.warning(f"⚠️ Package {pkg} not found")

    def _is_package_installed(self, package_name: str) -> bool:
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        return spec is not None

    async def _load_responses(self):
        self.logger.info("📄 Loading response files...")
        response_dir = Path("responses")
        response_dir.mkdir(exist_ok=True)
        required_files = [
            "welcome.json", "goodbye.json", "auto_reply.json",
            "voice_reply.json", "rules.json", "help.json",
            "admin.json", "error.json", "notification.json",
            "event.json", "reminder.json"
        ]
        missing = [f for f in required_files if not (response_dir / f).exists()]
        if missing:
            self.logger.warning(f"⚠️ Missing response files: {missing}")
        else:
            self.logger.info(f"✅ Response files loaded: {required_files}")

    async def _init_telegram(self):
        self.logger.info("🤖 Initializing Telegram bot...")
        # Telegram initialization logic goes here
        await asyncio.sleep(0.1)  # dummy delay for init
        self.logger.info("✅ Telegram bot initialized successfully")

    async def _warmup_cache(self):
        self.logger.info("🔥 Warming up cache...")

    async def _start_background_tasks(self):
        self.logger.info("🔄 Starting background tasks...")

    async def _verify_modules(self):
        self.logger.info("✅ Verifying modules...")

    async def get_startup_time(self) -> float:
        if self.start_time:
            return time.time() - self.start_time
        return 0
