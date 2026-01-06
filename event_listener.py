"""
Event Listener - Listens for Telegram events
"""

import logging
from typing import Dict, Any, Callable
from telegram import Update
from telegram.ext import Application, ContextTypes
from router import EventType

class EventListener:
    """Listens for Telegram events"""
    
    def __init__(self, token: str, dispatcher):
        self.logger = logging.getLogger("nomi_listener")
        self.token = token
        self.dispatcher = dispatcher
        self.app = None
        self.handlers = {}
        
    async def initialize(self):
        """Initialize Telegram application"""
        self.logger.info("📡 Initializing Telegram listener...")
        
        try:
            # Create application
            self.app = Application.builder().token(self.token).build()
            
            # Register handlers
            self._register_handlers()
            
            self.logger.info("✅ Telegram listener initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Telegram: {e}")
            raise
            
    def _register_handlers(self):
        """Register all Telegram handlers"""
        
        # Message handler
        async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self._handle_message(update, context)
        self.app.add_handler(telegram.ext.MessageHandler(
            telegram.ext.filters.ALL, message_handler
        ))
        
        # Command handler
        async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self._handle_command(update, context)
        self.app.add_handler(telegram.ext.CommandHandler(
            "start", command_handler
        ))
        
        # Callback query handler
        async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self._handle_callback(update, context)
        self.app.add_handler(telegram.ext.CallbackQueryHandler(callback_handler))
        
        # New chat members handler
        async def new_members_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await self._handle_new_members(update, context)
        self.app.add_handler(telegram.ext.ChatMemberHandler(
            new_members_handler, telegram.ext.ChatMemberHandler.CHAT_MEMBER
        ))
        
        self.logger.info("📝 Registered all handlers")
        
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            event_data = {
                "type": EventType.MESSAGE,
                "update": update,
                "context": context,
                "message": update.message,
                "user": update.effective_user,
                "chat": update.effective_chat,
                "text": update.message.text if update.message else None
            }
            
            await self.dispatcher.dispatch(EventType.MESSAGE, event_data)
            
        except Exception as e:
            self.logger.error(f"❌ Message handling error: {e}")
            
    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle commands"""
        try:
            event_data = {
                "type": EventType.COMMAND,
                "update": update,
                "context": context,
                "command": update.message.text.split()[0][1:],
                "args": update.message.text.split()[1:],
                "user": update.effective_user,
                "chat": update.effective_chat
            }
            
            await self.dispatcher.dispatch(EventType.COMMAND, event_data)
            
        except Exception as e:
            self.logger.error(f"❌ Command handling error: {e}")
            
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        try:
            event_data = {
                "type": EventType.CALLBACK_QUERY,
                "update": update,
                "context": context,
                "callback_query": update.callback_query,
                "data": update.callback_query.data
            }
            
            await self.dispatcher.dispatch(EventType.CALLBACK_QUERY, event_data)
            
        except Exception as e:
            self.logger.error(f"❌ Callback handling error: {e}")
            
    async def _handle_new_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new chat members"""
        try:
            event_data = {
                "type": EventType.NEW_MEMBERS,
                "update": update,
                "context": context,
                "new_members": update.message.new_chat_members,
                "chat": update.effective_chat
            }
            
            await self.dispatcher.dispatch(EventType.NEW_MEMBERS, event_data)
            
        except Exception as e:
            self.logger.error(f"❌ New members handling error: {e}")
            
    async def start(self):
        """Start listening for events"""
        if not self.app:
            await self.initialize()
            
        self.logger.info("👂 Starting to listen for events...")
        
        # Start polling
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        self.logger.info("✅ Event listener started")
        
    async def stop(self):
        """Stop listening"""
        if self.app:
            self.logger.info("🛑 Stopping event listener...")
            await self.app.stop()
            await self.app.shutdown()
            self.logger.info("✅ Event listener stopped")