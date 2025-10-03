import os
import asyncio
import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
import logging

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8436214881:AAH-9tb2VtTW27a0qvEF779pGgnIviZrdnY")
OWNER_ID = int(os.getenv("OWNER_ID", "8176816554"))
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://light3:light3@light3.iayn85q.mongodb.net/?retryWrites=true&w=majority&appName=light3")

# YOUR TELETHON SESSION
TELETHON_SESSION = "1BVtsOHwBuxP5qkQkntr33JYA_Yr9h6qXirgi3U3snfIUTK0fKZ2xl4vXs5GZ-kCZBZ_TM6e1aB8EFDZpN-gTSqtXhQMYR70enYx-u8oYeA-gR3SfSl6rkyTzJ0o-IPxaM5IY2rggySwewiRZ_JvCM6bPDtAe1ALcsnkcSd0G7O2xdd1xTYzgh3eE6H_Nb40lOeo95vNIRqu-EaNscQeTp8ohYhD0FstP4d-xa6f-Kmk45aO_EKSp-uCQPZs5hddPb_0U5GP5b2KtI0otLRwqLRx4rfS-XtN77ia1SZodg1OSH88s1Ag4ra7DH5iO-rXoMDFQ7oOlfyh7CIMP3PQsvlkRQwy53-g="

SUPPORT_GROUP = "https://t.me/+GVdNrsS5BnphMjU1"
SUPPORT_CHANNEL = "https://t.me/KIRA_BOTS"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB
try:
    mongo = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    mongo.server_info()
    db = mongo.userbot_manager
    users_db = db.users
    logger.info("✅ MongoDB Connected!")
except Exception as e:
    logger.error(f"❌ MongoDB Error: {e}")
    exit(1)

# Main Bot
app = Client("main_bot", bot_token=BOT_TOKEN, api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627")

# Global UserBot Client (using YOUR session)
userbot_client = None

# Start UserBot with your session
async def start_userbot():
    global userbot_client
    try:
        userbot_client = TelegramClient(
            StringSession(TELETHON_SESSION),
            2040,
            "b18441a1ff607e10a989891a5462e627"
        )
        
        @userbot_client.on(events.NewMessage(incoming=True))
        async def handle_incoming_message(event):
            if not event.is_private or event.message.out:
                return
            
            sender_id = event.sender_id
            user_data = users_db.find_one({"user_id": sender_id})
            
            if user_data and user_data.get("is_afk") and user_data.get("auto_reply_msg"):
                try:
                    await event.reply(user_data["auto_reply_msg"])
                    logger.info(f"✅ Auto-reply sent to {sender_id}")
                except Exception as e:
                    logger.error(f"❌ Reply failed: {e}")
        
        await userbot_client.start()
        logger.info("✅ UserBot Started with Your Session!")
        return True
    except Exception as e:
        logger.error(f"❌ UserBot failed: {e}")
        return False

# Start Command
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    
    welcome_text = f"""
🤖 **UserBot Auto-Reply Manager**

🚀 **Powered by Your Account**
• Auto-reply from main account
• Set any text/channel links
• Simple commands

⚡ **User Commands:**
.setreply [message] - Set auto-reply
.offreply - Turn off auto-reply  
.check - Check status
.help - Support & guide

📞 **Support:** {SUPPORT_GROUP}
    """
    
    await message.reply_text(welcome_text)
    
    users_db.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "join_date": datetime.datetime.now(),
            "is_afk": False
        }},
        upsert=True
    )

# .setreply command
@app.on_message(filters.command("setreply", prefixes="."))
async def setreply_cmd(client, message: Message):
    user_id = message.from_user.id
    
    if not userbot_client:
        await message.reply_text("❌ UserBot not running! Contact admin.")
        return
    
    reply_text = message.text.split('.setreply', 1)[1].strip()
    if not reply_text:
        await message.reply_text("❌ **Usage:** `.setreply Your message here`")
        return
    
    users_db.update_one(
        {"user_id": user_id},
        {"$set": {
            "auto_reply_msg": reply_text,
            "is_afk": True
        }}
    )
    
    await message.reply_text(f"✅ **Auto-Reply Set!**\n\n`{reply_text}`")

# .offreply command
@app.on_message(filters.command("offreply", prefixes="."))
async def offreply_cmd(client, message: Message):
    user_id = message.from_user.id
    
    users_db.update_one(
        {"user_id": user_id},
        {"$set": {"is_afk": False}}
    )
    
    await message.reply_text("❌ **Auto-Reply Turned Off!**")

# .check command
@app.on_message(filters.command("check", prefixes="."))
async def check_cmd(client, message: Message):
    user_id = message.from_user.id
    user_data = users_db.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply_text("❌ **No settings found!**")
        return
    
    status = "🟢 **ON**" if user_data.get("is_afk") else "🔴 **OFF**"
    message_text = user_data.get("auto_reply_msg", "Not set")
    
    await message.reply_text(
        f"📊 **Your Status:**\n\n"
        f"**Auto-Reply:** {status}\n"
        f"**Message:** `{message_text}`"
    )

# .help command
@app.on_message(filters.command("help", prefixes="."))
async def help_cmd(client, message: Message):
    help_text = f"""
🆘 **UserBot Help Guide**

⚡ **Commands:**
• `.setreply [message]` - Set auto-reply text/link
• `.offreply` - Turn off auto-reply
• `.check` - Check current status
• `.help` - Show this guide

💡 **How it works:**
1. Set your message with `.setreply`
2. When someone messages you, they get auto-reply
3. Your main account sends the reply

📞 **Support:** {SUPPORT_GROUP}
📢 **Channel:** {SUPPORT_CHANNEL}

🔒 **Powered by your account**
    """
    
    await message.reply_text(help_text)

# Broadcast command
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a message to broadcast.")
        return
    
    broadcast_msg = message.reply_to_message.text or message.reply_to_message.caption
    all_users = list(users_db.find())
    success = 0
    
    for user in all_users:
        try:
            await client.send_message(
                user["user_id"],
                f"📢 **Broadcast:**\n\n{broadcast_msg}"
            )
            success += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Broadcast failed for {user['user_id']}: {e}")
    
    await message.reply_text(f"✅ Broadcast sent to {success}/{len(all_users)} users.")

# Start everything
async def main():
    await app.start()
    logger.info("✅ Main Bot Started!")
    
    # Start UserBot
    if await start_userbot():
        logger.info("🚀 Both bots running!")
    else:
        logger.error("❌ UserBot failed to start!")
    
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
