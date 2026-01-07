import asyncio
import logging
import json
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ===============================
# Logging Setup
# ===============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("nomi_main")

# ===============================
# Load Config
# ===============================
CONFIG_PATH = Path("config/bot.json")
if not CONFIG_PATH.exists():
    logger.error("❌ bot.json config file missing!")
    exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config.get("token")
if not BOT_TOKEN:
    logger.error("❌ Telegram token not found in config/bot.json")
    exit(1)

# ===============================
# Load Response Files
# ===============================
RESPONSES_PATH = Path("responses")
responses = {}

for file in RESPONSES_PATH.glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        responses[file.stem] = json.load(f)
logger.info(f"✅ Response files loaded: {[f.stem for f in RESPONSES_PATH.glob('*.json')]}")

# ===============================
# Command Handlers
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.first_name
    welcome_text = responses.get("welcome", {}).get("start", f"হ্যালো {username}, NOMI বটে স্বাগতম!")
    # Example button
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Info", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = responses.get("help", {}).get("help", "এই বটে NOMI bot সাহায্য করবে!")
    await update.message.reply_text(help_text)

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    reply = None
    # Simple keyword match from auto_reply.json
    auto_data = responses.get("auto_reply", {})
    for key, value in auto_data.items():
        if key.lower() in text:
            reply = value
            break
    if reply:
        await update.message.reply_text(reply)

# ===============================
# CallbackQuery Handler (Buttons)
# ===============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        help_text = responses.get("help", {}).get("help", "এই বটে NOMI bot সাহায্য করবে!")
        await query.edit_message_text(help_text)
    elif query.data == "info":
        await query.edit_message_text("NOMI Bot v1.0.0 | Developed by You")

# ===============================
# Main Function
# ===============================
async def main():
    # Build application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    logger.info("🤖 NOMI is ONLINE")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()  # Keeps running until Ctrl+C

# ===============================
# Run
# ===============================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot stopped")
