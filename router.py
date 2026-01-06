"""
Router - Routes events to appropriate handlers
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

class EventType(Enum):
    """Event types enumeration"""
    MESSAGE = "message"
    CALLBACK_QUERY = "callback_query"
    INLINE_QUERY = "inline_query"
    CHAT_JOIN = "chat_join"
    CHAT_LEAVE = "chat_leave"
    NEW_MEMBERS = "new_members"
    LEFT_MEMBER = "left_member"
    VOICE = "voice"
    PHOTO = "photo"
    DOCUMENT = "document"
    COMMAND = "command"
    ERROR = "error"

class Router:
    """Routes events to handlers"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_router")
        self.handlers = {}
        self.middlewares = []
        
    def register_handler(self, event_type: EventType, handler):
        """Register an event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for {event_type}")
        
    def register_middleware(self, middleware):
        """Register middleware"""
        self.middlewares.append(middleware)
        self.logger.debug(f"Registered middleware: {middleware.__class__.__name__}")
        
    async def route(self, event_type: EventType, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Route an event to appropriate handlers
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Response data or None
        """
        self.logger.debug(f"📨 Routing event: {event_type}")
        
        # Apply middlewares
        for middleware in self.middlewares:
            data = await middleware.process(data)
            if data is None:
                self.logger.debug("Middleware blocked event")
                return None
                
        # Get handlers for event type
        handlers = self.handlers.get(event_type, [])
        
        if not handlers:
            self.logger.warning(f"No handler for event type: {event_type}")
            return None
            
        # Execute handlers
        responses = []
        for handler in handlers:
            try:
                response = await handler(data)
                if response:
                    responses.append(response)
            except Exception as e:
                self.logger.error(f"Handler error: {e}")
                
        # Merge responses if multiple
        if responses:
            if len(responses) == 1:
                return responses[0]
            # Logic to merge multiple responses
            return self._merge_responses(responses)
            
        return None
        
    def _merge_responses(self, responses: List[Dict]) -> Dict:
        """Merge multiple responses"""
        merged = {}
        for response in responses:
            merged.update(response)
        return merged
        
    def get_handler_count(self) -> Dict[EventType, int]:
        """Get count of handlers per event type"""
        return {et: len(handlers) for et, handlers in self.handlers.items()}