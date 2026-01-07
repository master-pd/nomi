#!/usr/bin/env python3
"""
𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 - Main Entry Point
Ultra Pro Max Enterprise Telegram Bot
"""

import asyncio
import logging
from bootstrap import Bootstrap
from startup import StartupManager
from shutdown import ShutdownManager
from healthcheck import HealthMonitor
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class NOMIBot:
    def __init__(self):
        self.logger = logging.getLogger("nomi_main")
        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()
        self.is_running = False
        self.app = None
        self.BOT_TOKEN = None
        self.ADMIN_IDS = []
        self.OWNER_ID = None

    async def get_credentials(self):
        """Terminal থেকে Bot Token, Admin ID, Owner ID নাও"""
        self.BOT_TOKEN = input("🔑 Enter your Telegram Bot Token: ").strip()
        admin_input = input("🛡️ Enter Admin IDs (comma separated): ").strip()
        self.ADMIN_IDS = [int(x.strip()) for x in admin_input.split(",") if x.strip().isdigit()]
        owner_input = input("👑 Enter Owner ID: ").strip()
        self.OWNER_ID = int(owner_input)

        self.logger.info("✅ Bot Token, Admin IDs, and Owner ID loaded successfully")

    async def start(self):
        """Start the bot"""
        try:
            await self.get_credentials()
            await self.bootstrap.initialize()
            await self.startup.execute()

            # Telegram bot setup
            self.logger.info("🤖 Initializing Telegram bot...")
            self.app = ApplicationBuilder().token(self.BOT_TOKEN).build()

            # Add basic /start command
            async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("✅ NOMI Bot is online!")

            self.app.add_handler(CommandHandler("start", start_cmd))

            # Initialize, start, and polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            self.logger.info("✅ Telegram bot initialized successfully")

            # Health Monitor
            asyncio.create_task(self.health.start_monitoring())

            self.is_running = True
            self.logger.info("✅ Bot successfully started!")

            # Keep running
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        self.logger.info("🛑 Stopping bot...")
        self.is_running = False

        # Shutdown Telegram bot
        if self.app:
            await self.app.updater.stop_polling()
            await self.app.stop()
            await self.app.shutdown()

        # Shutdown other modules
        await self.shutdown.execute()
        await self.bootstrap.cleanup()

        self.logger.info("👋 Bot stopped successfully")

async def main():
    bot = NOMIBot()

    # Handle clean shutdown
    import signal
    def handler(sig, frame):
        asyncio.create_task(bot.stop())
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
