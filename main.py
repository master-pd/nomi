#!/usr/bin/env python3
"""
𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 - Main Entry Point
Ultra Pro Max Enterprise Telegram Bot
"""

import asyncio
import sys
import logging
from pathlib import Path

from bootstrap import Bootstrap
from startup import StartupManager
from shutdown import ShutdownManager
from logger import setup_logger
from healthcheck import HealthMonitor
from version import __version__

# Telegram imports
from telegram.ext import ApplicationBuilder, CommandHandler

class NOMIBot:
    """Main Bot Class"""

    def __init__(self):
        self.logger = setup_logger("nomi_main")
        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()
        self.is_running = False
        self.application = None  # Telegram Application

    async def start(self):
        """Start the bot"""
        try:
            self.logger.info(f"🚀 NOMI v{__version__} Starting...")
            self.logger.info("🌍 Language: Bangla | ⏰ Timezone: Asia/Dhaka")

            # Bootstrap
            await self.bootstrap.initialize()

            # Startup
            await self.startup.execute()

            # Telegram bot initialization
            token = self.startup.config.get("token")
            if not token:
                self.logger.error("❌ Bot token missing in config!")
                return

            self.application = ApplicationBuilder().token(token).build()

            # Add a simple /start handler for testing
            async def start_command(update, context):
                await update.message.reply_text("✅ NOMI Bot is ONLINE!")

            self.application.add_handler(CommandHandler("start", start_command))

            # Start Telegram polling in background
            asyncio.create_task(self.application.initialize())
            asyncio.create_task(self.application.start())
            self.logger.info("✅ Telegram bot initialized successfully")

            # Health Monitor
            asyncio.create_task(self.health.start_monitoring())

            self.is_running = True
            self.logger.info("✅ Bot successfully started!")

            # Keep bot running
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        self.logger.info("🛑 Stopping bot...")
        self.is_running = False

        # Stop Telegram
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("✅ Telegram bot stopped")

        # Shutdown
        await self.shutdown.execute()

        # Cleanup
        await self.bootstrap.cleanup()

        self.logger.info("👋 Bot stopped successfully")


async def run_bot():
    bot = NOMIBot()

    # Handle Ctrl+C
    import signal
    def handler(sig, frame):
        asyncio.create_task(bot.stop())
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
