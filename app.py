import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Initialize Flask app for Render's web hosting requirement
app = Flask(__name__)

@app.route('/')
def home():
    return "QuickpickBot is running!"

# 2. Telegram Bot Logic
# A simple mock database of alternative products
PRODUCT_MATCHES = {
    "iphone": ["Samsung Galaxy S24", "Google Pixel 8", "OnePlus 12"],
    "shoes": ["Nike Air Max", "Adidas Ultraboost", "Puma Cali"],
    "laptop": ["MacBook Air M3", "Dell XPS 13", "Lenovo ThinkPad X1"]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting when the command /start is issued."""
    await update.message.reply_text(
        "👋 Welcome to QuickpickBot! \n\n"
        "Tell me what product you are looking for, or what just went out of stock, "
        "and I will suggest context-aware alternatives instantly so you never leave empty-handed!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyzes user input and suggests alternatives."""
    user_text = update.message.text.lower()
    found_match = False

    for key, alternatives in PRODUCT_MATCHES.items():
        if key in user_text:
            match_list = "\n• ".join(alternatives)
            response = (
                f"🔍 It looks like you're interested in items related to **{key.capitalize()}**.\n"
                f"Before you give up, check out these great, highly-rated matches available right now:\n\n"
                f"• {match_list}\n\n"
                "Would you like to view details or prices for any of these?"
            )
            await update.message.reply_text(response)
            found_match = True
            break

    if not found_match:
        await update.message.reply_text(
            "🤔 I couldn't find an exact match for that right now. "
            "Try typing a general category like 'shoes', 'iphone', or 'laptop'!"
        )

# 3. Main runner
def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No TELEGRAM_TOKEN provided.")
        return

    # Build the Telegram Application
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling for messages
    print("Bot is polling...")
    application.run_polling()

if __name__ == '__main__':
    # When running locally, you can run main() directly.
    # For Render, we rely on the background worker or a split setup.
    import threading
    # Run the Telegram bot in a background thread
    threading.Thread(target=main, daemon=True).start()
    # Run the Flask app on the port Render gives us
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
