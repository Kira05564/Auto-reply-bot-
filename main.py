import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = "8436214881:AAH-9tb2VtTW27a0qvEF779pGgnIviZrdnY"
API_ID = 22545644
API_HASH = "5b8f3b235407aea5242c04909e38d33d"
OWNER_ID = 8176816554
CHANNEL_USERNAME = "@KIRA_BOTS"
SUPPORT_GROUP = "https://t.me/+qf33ETc6YDplYzk1"
MAX_USERS = 5

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, session_string TEXT, status TEXT, join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/KIRA_BOTS")],
        [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 **Hello {name}!**\n\n"
        "🤖 **Auto Reply UserBot Setup**\n\n"
        "📝 **Steps to use:**\n"
        "1. Join our channel (Required)\n"  
        "2. Verify your join\n"
        "3. Send your session string\n"
        "4. Start auto replying!\n\n"
        "🔒 **User Limit:** 5 users only\n"
        "📢 **Support:** @KIRA_BOTS",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Check user count
    c.execute("SELECT COUNT(*) FROM users WHERE status='active'")
    user_count = c.fetchone()[0]
    
    if user_count >= MAX_USERS:
        await query.edit_message_text(
            "❌ **User Limit Reached!**\n\n"
            f"Currently {MAX_USERS}/{MAX_USERS} users active.\n"
            "Please try again later."
        )
        return
    
    await query.edit_message_text(
        "🎉 **Verification Successful!**\n\n"
        "📲 **Now create your session string:**\n\n"
        "1. Go to 👉 @StringSessionGenBot\n"
        "2. Select **Telegram** → **User Account**\n"
        "3. Copy the generated string\n"
        "4. Send it here like this:\n"
        "`abcd1234...` (session string)\n\n"
        "⚠️ **Warning:** Don't share session with anyone!\n"
        "🔒 Your data is secure with us.",
        parse_mode="Markdown"
    )

async def handle_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session_string = update.message.text.strip()
    
    # Check if session string looks valid
    if len(session_string) < 50:
        await update.message.reply_text(
            "❌ **Invalid Session String!**\n\n"
            "Please make sure you copied the complete session string from @StringSessionGenBot"
        )
        return
    
    # Check user count
    c.execute("SELECT COUNT(*) FROM users WHERE status='active'")
    user_count = c.fetchone()[0]
    
    if user_count >= MAX_USERS:
        await update.message.reply_text(
            "❌ **User Limit Reached!**\n\n"
            f"Currently {MAX_USERS}/{MAX_USERS} users active.\n"
            "Please try again later."
        )
        return
    
    # Check if user already exists
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = c.fetchone()
    
    if existing_user:
        # Update existing user
        c.execute("UPDATE users SET session_string=?, status='active' WHERE user_id=?", 
                 (session_string, user_id))
    else:
        # Add new user
        c.execute("INSERT INTO users (user_id, session_string, status) VALUES (?, ?, ?)", 
                 (user_id, session_string, "active"))
    
    conn.commit()
    
    await update.message.reply_text(
        "✅ **UserBot Activated Successfully!**\n\n"
        "🤖 **Your auto-reply bot is now starting...**\n\n"
        "📋 **Available Commands in your UserBot:**\n"
        "• `.setreply <message>` - Set auto reply\n"
        "• `.offreply` - Turn off auto reply\n"  
        "• `.check` - Check current reply\n"
        "• `.help` - Help guide\n\n"
        "💬 **Now when someone DMs you, they'll get your auto-reply!**\n"
        "📢 **Support:** @KIRA_BOTS",
        parse_mode='Markdown'
    )
    
    # Start userbot in background
    try:
        from userbot_manager import userbot_manager
        await userbot_manager.add_user(user_id, session_string)
    except Exception as e:
        logger.error(f"Failed to start userbot for {user_id}: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **Auto Reply Bot Help**

**For Main Bot:**
/start - Start the bot and setup
/help - Show this help message

**For Your UserBot (After Setup):**
.setreply <message> - Set auto reply message
.offreply - Turn off auto reply  
.check - Check current auto reply
.help - Show userbot help

**Support:**
📢 Channel: @KIRA_BOTS
👥 Group: https://t.me/+qf33ETc6YDplYzk1

**Note:** Only 5 users can use this service simultaneously.
    """
    await update.message.reply_text(help_text)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(verify_join, pattern="verify_join"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_session))
    
    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()
