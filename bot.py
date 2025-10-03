import os
import asyncio
import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService
from pymongo import MongoClient
import logging

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8436214881:AAH-9tb2VtTW27a0qvEF779pGgnIviZrdnY")
OWNER_ID = int(os.getenv("OWNER_ID", "8176816554"))
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://light3:light3@light3.iayn85q.mongodb.net/?retryWrites=true&w=majority&appName=light3")
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

SUPPORT_GROUP = "https://t.me/+GVdNrsS5BnphMjU1"
SUPPORT_CHANNEL = "https://t.me/KIRA_BOTS"
MAX_USERBOTS = 10  # Render limit

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
app = Client("main_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Active sessions
user_sessions = {}
active_userbots = {}

# Start Command
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    total_users = users_db.count_documents({})
    
    welcome_text = f"""
🤖 **UserBot Auto-Reply Manager**

🚀 **Create your personal UserBot:**
• Auto-reply from YOUR account
• Set any text/channel links
• Simple commands

⚡ **Commands:**
`.setreply [message]` - Set auto-reply
`.offreply` - Turn off auto-reply  
`.check` - Check status
`.help` - Support & guide

📊 **Stats:** {total_users}/{MAX_USERBOTS} Users

🔐 **100% Secure** - Your data is encrypted

📞 **Support:** {SUPPORT_GROUP}
    """
    
    await message.reply_text(welcome_text)
    
    users_db.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "join_date": datetime.datetime.now()
        }},
        upsert=True
    )

# Login Command
@app.on_message(filters.command("login"))
async def login_cmd(client, message: Message):
    user_id = message.from_user.id
    
    # Check user limit
    if users_db.count_documents({"session_string": {"$exists": True}}) >= MAX_USERBOTS:
        await message.reply_text(f"❌ **User Limit Reached!**\n\nOnly {MAX_USERBOTS} users can create UserBots.\nTry again later.")
        return
    
    user_sessions[user_id] = {"step": "phone"}
    await message.reply_text("📱 **Send your phone number:**\n\nFormat: `+919876543210`")

# Handle Phone Number
@app.on_message(filters.regex(r'^\+[\d]+$') & filters.private)
async def handle_phone(client, message: Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)
    
    if session and session.get("step") == "phone":
        phone = message.text
        user_sessions[user_id] = {"step": "code", "phone": phone}
        
        try:
            user_client = TelegramClient(StringSession(), API_ID, API_HASH)
            await user_client.connect()
            sent_code = await user_client.send_code_request(phone)
            
            user_sessions[user_id]["client"] = user_client
            user_sessions[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            
            await message.reply_text("🔐 **OTP Sent!**\n\nSend code in format:\n`1 2 3 4 5`")
            
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            user_sessions.pop(user_id, None)

# Handle OTP Code
@app.on_message(filters.regex(r'^[\d\s]+$') & filters.private)
async def handle_code(client, message: Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)
    
    if session and session.get("step") == "code":
        code = message.text.replace(" ", "")
        user_client = session["client"]
        phone_code_hash = session["phone_code_hash"]
        
        try:
            await user_client.sign_in(session["phone"], code, phone_code_hash=phone_code_hash)
            await handle_successful_login(user_client, user_id, session["phone"])
            
        except Exception as e:
            if "password" in str(e):
                user_sessions[user_id]["step"] = "password"
                await message.reply_text("🔒 **2-Step Verification!**\nSend your password:")
            else:
                await message.reply_text("❌ Invalid code! Use /login again")
                user_sessions.pop(user_id, None)

# Handle Password
@app.on_message(filters.private)
async def handle_password(client, message: Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)
    
    if session and session.get("step") == "password":
        password = message.text
        user_client = session["client"]
        
        try:
            await user_client.sign_in(password=password)
            await handle_successful_login(user_client, user_id, session["phone"])
            
        except Exception as e:
            await message.reply_text(f"❌ Login failed: {str(e)}")
            user_sessions.pop(user_id, None)

async def handle_successful_login(user_client, user_id, phone):
    session_string = user_client.session.save()
    
    users_db.update_one(
        {"user_id": user_id},
        {"$set": {
            "phone": phone,
            "session_string": session_string,
            "login_date": datetime.datetime.now(),
            "is_afk": False,
            "auto_reply_msg": ""
        }}
    )
    
    await user_client.disconnect()
    user_sessions.pop(user_id, None)
    
    # Start UserBot
    await start_userbot(user_id)
    
    await app.send_message(
        user_id,
        "🎉 **UserBot Created Successfully!**\n\n"
        "Now use these commands in ANY chat:\n\n"
        "`.setreply Hello, I'm AFK`\n"
        "`.offreply` - Turn off\n"
        "`.check` - Check status\n"
        "`.help` - Support\n\n"
        "**Your account will now auto-reply!**"
    )

# Start UserBot
async def start_userbot(user_id):
    try:
        user_data = users_db.find_one({"user_id": user_id})
        if not user_data or not user_data.get("session_string"):
            return
        
        session_string = user_data["session_string"]
        user_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        
        @user_client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not event.is_private or event.message.out:
                return
            
            user_data = users_db.find_one({"user_id": user_id})
            if user_data and user_data.get("is_afk") and user_data.get("auto_reply_msg"):
                await event.reply(user_data["auto_reply_msg"])
        
        await user_client.start()
        active_userbots[user_id] = user_client
        logger.info(f"✅ UserBot started for {user_id}")
        
    except Exception as e:
        logger.error(f"❌ UserBot error for {user_id}: {e}")

# .setreply command
@app.on_message(filters.command("setreply", prefixes="."))
async def setreply_cmd(client, message: Message):
    user_id = message.from_user.id
    user_data = users_db.find_one({"user_id": user_id})
    
    if not user_data or not user_data.get("session_string"):
        await message.reply_text("❌ **No UserBot Found!**\nUse /login to create one.")
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
    
    if user_id not in active_userbots:
        await start_userbot(user_id)
    
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
        await message.reply_text("❌ **No UserBot Found!**")
        return
    
    status = "🟢 **ON**" if user_data.get("is_afk") else "🔴 **OFF**"
    message_text = user_data.get("auto_reply_msg", "Not set")
    
    await message.reply_text(
        f"📊 **UserBot Status:**\n\n"
        f"**Status:** {status}\n"
        f"**Message:** `{message_text}`\n\n"
        f"**Phone:** `{user_data.get('phone', 'N/A')}`"
    )

# .help command
@app.on_message(filters.command("help", prefixes="."))
async def help_cmd(client, message: Message):
    help_text = f"""
🆘 **UserBot Help Guide**

📱 **Setup Steps:**
1. Use `/login` in this chat
2. Send your phone number
3. Enter OTP code
4. Set password (if any)

⚡ **Commands:**
• `.setreply [message]` - Set auto-reply text/link
• `.offreply` - Turn off auto-reply
• `.check` - Check current status
• `.help` - Show this guide

💡 **Tips:**
• You can use channel/group links
• No message length limits
• Works in all private chats

📞 **Support:** {SUPPORT_GROUP}
📢 **Channel:** {SUPPORT_CHANNEL}

🔒 **Your data is 100% secure!**
    """
    
    await message.reply_text(help_text)

# Broadcast command (Owner only)
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a message to broadcast.")
        return
    
    broadcast_msg = message.reply_to_message.text or message.reply_to_message.caption
    if not broadcast_msg:
        await message.reply_text("❌ No text found in message.")
        return
    
    all_users = list(users_db.find())
    success = 0
    
    for user in all_users:
        try:
            await client.send_message(
                user["user_id"],
                f"📢 **Broadcast from Admin:**\n\n{broadcast_msg}"
            )
            success += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Broadcast failed for {user['user_id']}: {e}")
    
    await message.reply_text(f"✅ Broadcast sent to {success}/{len(all_users)} users.")

if __name__ == "__main__":
    logger.info("🚀 Starting UserBot Manager...")
    app.run()