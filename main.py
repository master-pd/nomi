#!/usr/bin/env python3
"""
𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 - Main Entry Point (Production)
Ultra Pro Max Enterprise Telegram Bot
Supports terminal input for Bot Token, Admin ID, Owner ID
Handles large-scale tools (500+ lines)
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

class NOMIBot:
    """Main Bot Class"""
    
    def __init__(self, bot_token: str, admin_id: int, owner_id: int):
        self.logger = setup_logger("nomi_main")
        self.bootstrap = Bootstrap()
        self.startup = StartupManager(bot_token=bot_token, admin_id=admin_id, owner_id=owner_id)
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()
        self.is_running = False
        self.bot_token = bot_token
        self.admin_id = admin_id
        self.owner_id = owner_id
        
    async def start(self):
        """Start the bot"""
        try:
            self.logger.info(f"🚀 𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬 v{__version__} Starting...")
            self.logger.info("🔧 System: Ultra Pro Max Enterprise")
            self.logger.info("🌍 Language: Bangla")
            self.logger.info("⏰ Timezone: Asia/Dhaka")
            
            # Bootstrap initialization
            await self.bootstrap.initialize()
            
            # Startup sequence (loads tools, engines, Telegram bot)
            await self.startup.execute()
            
            # Start health monitoring in background
            asyncio.create_task(self.health.start_monitoring())
            
            self.is_running = True
            self.logger.info("✅ Bot successfully started!")
            
            # Keep bot running indefinitely
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot: {e}")
            await self.stop()
            
    async def stop(self):
        """Stop the bot"""
        self.logger.info("🛑 Stopping bot...")
        self.is_running = False
        
        # Shutdown sequence
        await self.shutdown.execute()
        
        # Cleanup resources
        await self.bootstrap.cleanup()
        
        self.logger.info("👋 Bot stopped successfully")
        
async def run_bot(bot_token: str, admin_id: int, owner_id: int):
    bot = NOMIBot(bot_token=bot_token, admin_id=admin_id, owner_id=owner_id)

    # Signal handler for clean shutdown
    import signal
    def handler(sig, frame):
        asyncio.create_task(bot.stop())
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    await bot.start()

def get_user_input():
    """Prompt terminal input for Bot Token, Admin ID, Owner ID"""
    print("\n📝 Enter Bot Configuration\n")
    bot_token = input("Enter Telegram Bot Token: ").strip()
    
    while True:
        try:
            admin_id = int(input("Enter Admin ID (Telegram numeric ID): ").strip())
            break
        except ValueError:
            print("❌ Invalid ID. Must be a number.")
            
    while True:
        try:
            owner_id = int(input("Enter Owner ID (Telegram numeric ID): ").strip())
            break
        except ValueError:
            print("❌ Invalid ID. Must be a number.")
            
    print("\n✅ Configuration accepted!")
    return bot_token, admin_id, owner_id

if __name__ == "__main__":
    try:
        # Terminal input
        bot_token, admin_id, owner_id = get_user_input()
        
        # Start bot
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(run_bot(bot_token, admin_id, owner_id))
            loop.run_forever()
        except RuntimeError:
            asyncio.run(run_bot(bot_token, admin_id, owner_id))
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
