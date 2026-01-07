#!/usr/bin/env python3
"""
𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 - Main Entry Point
Ultra Pro Max Enterprise Telegram Bot
"""

import asyncio
import sys
import logging
from pathlib import Path

# Ensure project root in path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ===== Core Imports =====
from bootstrap import Bootstrap
from startup import StartupManager
from shutdown import ShutdownManager
from logger import setup_logger
from healthcheck import HealthMonitor

from dispatcher import Dispatcher
from router import Router, EventType

# ===== Telegram Imports =====
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

from config.bot import BOT_TOKEN
from version import __version__


class NOMIBot:
    """Main Bot Controller"""

    def __init__(self):
        self.logger = setup_logger("nomi_main")

        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()

        self.application: Application | None = None
        self.dispatcher: Dispatcher | None = None
        self.router: Router | None = None

    # =======================
    # Telegram Handlers
    # =======================

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all incoming messages"""
        try:
            if not update.message:
                return

            event_data = {
                "chat_id": update.message.chat_id,
                "user_id": update.message.from_user.id if update.message.from_user else None,
                "text": update.message.text,
                "message": update.message,
                "update": update,
                "context": context,
            }

            await self.dispatcher.dispatch(EventType.MESSAGE, event_data)

        except Exception as e:
            self.logger.exception(f"Message handler error: {e}")

    async def on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ /start command """
        await update.message.reply_text(
            "🤖 𝗡𝗢𝗠𝗜 Bot is online!\n\n"
            "আমি এখন প্রস্তুত। মেসেজ পাঠাও 🙂"
        )

    # =======================
    # Startup
    # =======================

    async def start(self):
        """Start bot system"""
        self.logger.info(f"🚀 NOMI v{__version__} starting...")
        self.logger.info("🌍 Language: Bangla | ⏰ Timezone: Asia/Dhaka")

        # Bootstrap
        await self.bootstrap.initialize()

        # Startup sequence
        await self.startup.execute()

        # Router & Dispatcher
        self.router = Router()
        self.dispatcher = Dispatcher(self.router)
        await self.dispatcher.start()

        # Telegram Application
        self.application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        # Register Handlers
        self.application.add_handler(CommandHandler("start", self.on_start))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_message)
        )

        # Health Monitor
        asyncio.create_task(self.health.start_monitoring())

        self.logger.info("✅ Bot fully initialized")
        self.logger.info("🤖 NOMI is ONLINE")

        # Run bot
        await self.application.initialize()
        await self.application.start()
        await self.application.bot.initialize()
        await self.application.bot.get_me()

        await self.application.updater.start_polling()
        await self.application.wait_closed()

    # =======================
    # Shutdown
    # =======================

    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("🛑 Shutting down bot...")

        if self.application:
            await self.application.stop()
            await self.application.shutdown()

        await self.shutdown.execute()
        await self.bootstrap.cleanup()

        self.logger.info("👋 Bot stopped cleanly")


# =======================
# Entry Point
# =======================

async def main():
    bot = NOMIBot()

    loop = asyncio.get_running_loop()

    # Signals
    import signal

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.stop()))

    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
