#!/usr/bin/env python3
"""
𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 - Main Entry Point
Ultra Pro Max Enterprise Telegram Bot
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from bootstrap import Bootstrap
from startup import StartupManager
from shutdown import ShutdownManager
from logger import setup_logger
from healthcheck import HealthMonitor
from version import __version__

# Telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load bot token
from config.bot import BOT_TOKEN

# Load responses
import json
RESPONSES = {}
resp_dir = Path("responses")
if resp_dir.exists():
    for f in resp_dir.glob("*.json"):
        with open(f, "r", encoding="utf-8") as file:
            RESPONSES[f.stem] = json.load(file)

# Example command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = RESPONSES.get("welcome", {}).get("text", "𝗡𝗢𝗠𝗜 Bot is active! ✅")
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = RESPONSES.get("help", {}).get("text", "This is the help message.")
    await update.message.reply_text(text)


class NOMIBot:
    """Main Bot Class"""
    
    def __init__(self):
        self.logger = setup_logger("nomi_main")
        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()
        self.is_running = False
        self.app = ApplicationBuilder().token(BOT_TOKEN).build()
        # Register Telegram commands
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("help", help_command))
        
    async def start(self):
        """Start the bot"""
        try:
            self.logger.info(f"🚀 𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 v{__version__} Starting...")
            self.logger.info("🔧 System: Ultra Pro Max Enterprise")
            self.logger.info("🌍 Language: Bangla")
            self.logger.info("⏰ Timezone: Asia/Dhaka")
            
            # Bootstrap
            await self.bootstrap.initialize()
            
            # Startup
            await self.startup.execute()
            
            # Health Monitor
            asyncio.create_task(self.health.start_monitoring())
            
            self.is_running = True
            self.logger.info("✅ Bot successfully started!")
            
            # Start Telegram polling
            await self.app.run_polling()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            await self.stop()
            
    async def stop(self):
        """Stop the bot"""
        self.logger.info("🛑 Stopping bot...")
        self.is_running = False
        
        # Shutdown
        await self.shutdown.execute()
        
        # Cleanup
        await self.bootstrap.cleanup()
        
        self.logger.info("👋 Bot stopped successfully")
        sys.exit(0)
        
    def restart(self):
        """Restart the bot"""
        self.logger.info("🔄 Restarting bot...")
        # Implementation for restart


async def main():
    """Main function"""
    bot = NOMIBot()
    
    # Handle signals
    import signal
    def signal_handler(sig, frame):
        asyncio.create_task(bot.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot
    await bot.start()

if __name__ == "__main__":
    import asyncio
    import signal

    bot = NOMIBot()

    async def run_bot():
        # Handle signals
        def signal_handler(sig, frame):
            asyncio.create_task(bot.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await bot.start()

    try:
        # Get running loop or create new
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
