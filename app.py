import os
import json
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Initialize Flask
app = Flask(__name__)

# Mock database of alternative products
PRODUCT_MATCHES = {
    "iphone": ["Samsung Galaxy S24", "Google Pixel 8", "OnePlus 12"],
    "shoes": ["Nike Air Max", "Adidas Ultraboost", "Puma Cali"],
    "laptop": ["MacBook Air M3", "Dell XPS 13", "Lenovo ThinkPad X1"]
}

# 2. Initialize Telegram Application globally (without starting it yet)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# RENDER_EXTERNAL_URL is automatically provided by Render
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 

telegram_app = Application.builder().token(TOKEN).build()

# 3. Define Bot Command & Message Handlers
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

# Register handlers to the application
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 4. Flask Routes
@app.route('/')
def home():
    return "QuickpickBot Webhook Server is Live!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Endpoint that receives updates from Telegram and processes them."""
    if request.method == "POST":
        try:
            # Parse the update JSON from Telegram
            json_string = request.get_data().decode('utf-8')
            update = Update.de_json(json.loads(json_string), telegram_app.bot)
            
            # Feed the update into the telegram application framework
            await telegram_app.initialize()
            await telegram_app.process_update(update)
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print(f"Error processing update: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET', 'POST'])
async def set_webhook():
    """Helper route to register your Render URL with Telegram."""
    if not TOKEN or not RENDER_URL:
        return "Error: Missing configuration environment variables.", 400
    
    # Target URL Telegram will send messages to
    webhook_url = f"{RENDER_URL.rstrip('/')}/webhook"
    
    await telegram_app.initialize()
    success = await telegram_app.bot.set_webhook(url=webhook_url)
    
    if success:
        return f"Success: Webhook pointed to {webhook_url}", 200
    else:
        return "Failed to set webhook.", 500

if __name__ == '__main__':
    # Used only for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
