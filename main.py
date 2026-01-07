#!/usr/bin/env python3
"""
Main entry point for NOMI Bot
"""

import asyncio
import logging
from pathlib import Path

from bootstrap import Bootstrap
from startup import StartupManager
from dispatcher import Dispatcher
from router import Router, EventType

# ============================================
# Logging setup
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nomi_main")

# ============================================
# Main bot class
# ============================================
class NomiBot:
    def __init__(self):
        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.router = Router()
        self.dispatcher = Dispatcher(self.router)
        self.loop = asyncio.get_event_loop()
        self.bot_token = None

    async def start(self):
        try:
            logger.info("🚀 NOMI vv1.0.0-build1 Starting...")
            logger.info("🌍 Language: Bangla | ⏰ Timezone: Asia/Dhaka")

            # Bootstrap system
            await self.bootstrap.initialize()

            # Startup sequence
            await self.startup.execute()

            # Save token from startup config
            self.bot_token = self.startup.config.get("telegram_token")
            if not self.bot_token:
                raise ValueError("❌ Telegram token not found in config/bot.json")

            # Start dispatcher
            await self.dispatcher.start()

            logger.info("✅ Bot fully initialized")
            logger.info("🤖 NOMI is ONLINE")

            # Keep running until Ctrl+C
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("🛑 Stopping bot...")
            await self.shutdown()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            await self.shutdown()

    async def shutdown(self):
        logger.info("🛑 Starting shutdown sequence...")
        # Cleanup resources
        await self.bootstrap.cleanup()
        logger.info("👋 Bot stopped successfully")


# ============================================
# Entry point
# ============================================
if __name__ == "__main__":
    bot = NomiBot()
    asyncio.run(bot.start())
