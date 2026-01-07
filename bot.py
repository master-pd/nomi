# bot.py
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram import Update
from config.bot import BOT_TOKEN

class TelegramBot:
    def __init__(self):
        self.logger = logging.getLogger("nomi_telegram")
        self.app = Application.builder().token(BOT_TOKEN).build()

        # Handlers
        self.app.add_handler(CommandHandler("start", self.start_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_msg))

    async def start(self):
        """Start telegram polling"""
        self.logger.info("📡 Starting Telegram polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.bot.initialize()
        await self.app.updater.start_polling()
        self.logger.info("✅ Telegram polling started")

    async def stop(self):
        self.logger.info("🛑 Stopping Telegram bot...")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("✅ 𝗡𝗢𝗠𝗜 Bot is Online!")

    async def text_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"💬 You said:\n{update.message.text}")
