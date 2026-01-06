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

class NOMIBot:
    """Main Bot Class"""
    
    def __init__(self):
        self.logger = setup_logger("nomi_main")
        self.bootstrap = Bootstrap()
        self.startup = StartupManager()
        self.shutdown = ShutdownManager()
        self.health = HealthMonitor()
        self.is_running = False
        
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
            self.health.start_monitoring()
            
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
    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")