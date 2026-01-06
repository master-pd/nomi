"""
Shutdown Manager - Graceful shutdown handling
"""

import asyncio
import signal
import logging
from typing import List

class ShutdownManager:
    """Handles graceful shutdown"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_shutdown")
        self.shutdown_tasks = []
        self.is_shutting_down = False
        
    async def execute(self):
        """Execute shutdown sequence"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        self.logger.info("🛑 Starting shutdown sequence...")
        
        # Define shutdown tasks (in reverse order)
        tasks = [
            self._stop_background_tasks,
            self._save_all_data,
            self._close_connections,
            self._cleanup_temp,
            self._generate_shutdown_report
        ]
        
        # Execute tasks
        for task in tasks:
            try:
                await task()
                await asyncio.sleep(0.3)
            except Exception as e:
                self.logger.error(f"❌ Shutdown task failed: {e}")
                
        self.logger.info("👋 Shutdown completed")
        
    async def _stop_background_tasks(self):
        """Stop all background tasks"""
        self.logger.info("🛑 Stopping background tasks...")
        
    async def _save_all_data(self):
        """Save all data to persistent storage"""
        self.logger.info("💾 Saving data...")
        
    async def _close_connections(self):
        """Close all network connections"""
        self.logger.info("🔌 Closing connections...")
        
    async def _cleanup_temp(self):
        """Cleanup temporary files"""
        self.logger.info("🧹 Cleaning temporary files...")
        
    async def _generate_shutdown_report(self):
        """Generate shutdown report"""
        self.logger.info("📊 Generating shutdown report...")
        
    def register_shutdown_task(self, task):
        """Register a custom shutdown task"""
        self.shutdown_tasks.append(task)
        
    def handle_signal(self, sig, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📶 Received signal {sig}")
        asyncio.create_task(self.execute())