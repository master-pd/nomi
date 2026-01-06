#!/usr/bin/env python3
"""
Main runner file for Your Crush Bot
"""

import asyncio
import signal
import sys
from datetime import datetime

from config import Config
from main import YourCrushBot
from utils.logger_utils import setup_logger

logger = setup_logger()

class BotRunner:
    """Professional bot runner with graceful shutdown"""
    
    def __init__(self):
        self.bot_instance = None
        self.shutdown_event = asyncio.Event()
        
    async def run(self):
        """Run the bot"""
        try:
            logger.info("🚀 Starting Your Crush Bot...")
            
            # Create bot instance
            self.bot_instance = YourCrushBot()
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start bot
            await self.bot_instance.run()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        if sys.platform != 'win32':
            # Unix-like systems
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        else:
            # Windows
            pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_event.set()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down bot...")
        
        try:
            # Add any cleanup tasks here
            # Example: Close database connections, cleanup temp files, etc.
            
            logger.info("✅ Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        # Exit the program
        sys.exit(0)

def main():
    """Main entry point"""
    runner = BotRunner()
    
    try:
        # Run the bot
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()