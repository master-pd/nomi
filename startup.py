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

    async def execute(self):
        """Execute startup sequence"""
        self.start_time = time.time()
        self.logger.info("🚀 Executing startup sequence...")

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
                await asyncio.sleep(0.3)  # small delay between tasks
            except Exception as e:
                self.logger.error(f"❌ Startup task failed: {e}")
                raise

        elapsed = time.time() - self.start_time
        self.logger.info(f"✅ Startup completed in {elapsed:.2f} seconds")

    async def _check_requirements(self):
        """Check system requirements"""
        self.logger.info("🔍 Checking system requirements...")
        import sys

        # Python version check
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")

        # Required packages
        required_packages = [
            "telegram",  # Telegram bot API
            "PIL",       # Pillow
            "aiofiles",
            "aiohttp"
        ]

        for pkg in required_packages:
            if not self._is_package_installed(pkg):
                self.logger.warning(f"⚠️ Package {pkg} not found")

    def _is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed"""
        spec = importlib.util.find_spec(package_name)
        return spec is not None

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

        missing = [f for f in required_files if not (response_dir / f).exists()]
        if missing:
            self.logger.warning(f"⚠️ Missing response files: {missing}")

    async def _init_telegram(self):
        """Initialize Telegram bot"""
        self.logger.info("🤖 Initializing Telegram bot...")
        # Telegram bot init logic goes here
        # e.g., import telegram and initialize with token

    async def _warmup_cache(self):
        """Warm up cache systems"""
        self.logger.info("🔥 Warming up cache...")

    async def _start_background_tasks(self):
        """Start background tasks"""
        self.logger.info("🔄 Starting background tasks...")

    async def _verify_modules(self):
        """Verify all modules are loaded"""
        self.logger.info("✅ Verifying modules...")

    async def get_startup_time(self) -> float:
        """Get startup duration"""
        if self.start_time:
            return time.time() - self.start_time
        return 0
