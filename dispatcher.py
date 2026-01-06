"""
Dispatcher - Dispatches events to engines
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from router import Router, EventType

class Dispatcher:
    """Dispatches events to appropriate engines"""
    
    def __init__(self, router: Router):
        self.logger = logging.getLogger("nomi_dispatcher")
        self.router = router
        self.engines = {}
        self.event_queue = asyncio.Queue(maxsize=1000)
        
    def register_engine(self, engine_name: str, engine):
        """Register an engine"""
        self.engines[engine_name] = engine
        self.logger.info(f"🚀 Registered engine: {engine_name}")
        
    async def start(self):
        """Start dispatcher"""
        self.logger.info("🚦 Starting dispatcher...")
        # Start event processing task
        asyncio.create_task(self._process_events())
        
    async def dispatch(self, event_type: EventType, data: Dict[str, Any]):
        """
        Dispatch an event
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            # Put event in queue
            await self.event_queue.put((event_type, data))
            self.logger.debug(f"📤 Dispatched event: {event_type}")
        except asyncio.QueueFull:
            self.logger.warning("⚠️ Event queue full, dropping event")
            
    async def _process_events(self):
        """Process events from queue"""
        self.logger.info("🔄 Event processor started")
        
        while True:
            try:
                # Get event from queue
                event_type, data = await self.event_queue.get()
                
                # Route event
                response = await self.router.route(event_type, data)
                
                if response:
                    # Send to appropriate engine based on response
                    await self._send_to_engine(response)
                    
                # Mark task as done
                self.event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"❌ Event processing error: {e}")
                
    async def _send_to_engine(self, response: Dict[str, Any]):
        """Send response to appropriate engine"""
        engine_type = response.get("engine")
        
        if engine_type and engine_type in self.engines:
            engine = self.engines[engine_type]
            try:
                await engine.handle(response)
                self.logger.debug(f"📨 Sent to engine: {engine_type}")
            except Exception as e:
                self.logger.error(f"❌ Engine {engine_type} error: {e}")
        else:
            self.logger.warning(f"⚠️ No engine for type: {engine_type}")
            
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.event_queue.qsize()
        
    def get_engine_names(self) -> list:
        """Get list of registered engines"""
        return list(self.engines.keys())