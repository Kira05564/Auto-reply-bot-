import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import sqlite3

logger = logging.getLogger(__name__)

# Configuration
API_ID = 22545644
API_HASH = "5b8f3b235407aea5242c04909e38d33d"
MAX_USERS = 5

class UserBot:
    def __init__(self, session_string, user_id):
        self.session_string = session_string
        self.user_id = user_id
        self.client = None
        self.auto_reply_msg = "I'm offline right now. I'll reply later."
        self.is_running = False
        
    async def start(self):
        try:
            self.client = TelegramClient(
                StringSession(self.session_string), 
                API_ID, 
                API_HASH
            )
            
            await self.client.start()
            self.is_running = True
            logger.info(f"UserBot started for user {self.user_id}")
            
            # Setup event handlers
            self.client.add_event_handler(self.handle_incoming, events.NewMessage(incoming=True))
            self.client.add_event_handler(self.handle_commands, events.NewMessage(pattern=r'\.\w+'))
            
            # Send startup message
            await self.client.send_message(self.user_id, 
                "✅ **Your Auto-Reply UserBot is Now Active!**\n\n"
                "🤖 **Available Commands:**\n"
                "`.setreply <message>` - Set auto reply\n"
                "`.offreply` - Turn off auto reply\n"
                "`.check` - Check current reply\n"
                "`.help` - Show help guide\n\n"
                "💬 I'll auto-reply to your DMs now!"
            )
            
        except Exception as e:
            logger.error(f"Failed to start UserBot for {self.user_id}: {e}")
            self.is_running = False
            
    async def handle_incoming(self, event):
        if not event.is_private:
            return
            
        sender = await event.get_sender()
        if sender.bot:
            return
            
        me = await self.client.get_me()
        if event.sender_id == me.id:
            return
            
        if self.auto_reply_msg:
            try:
                await event.reply(self.auto_reply_msg)
                logger.info(f"Auto-replied to {event.sender_id}")
            except Exception as e:
                logger.error(f"Failed to auto-reply: {e}")
    
    async def handle_commands(self, event):
        if not event.is_private:
            return
            
        me = await self.client.get_me()
        if event.sender_id != me.id:
            return
            
        text = event.text
        if text.startswith('.setreply '):
            self.auto_reply_msg = text.replace('.setreply ', '')
            await event.reply(f"✅ **Auto Reply Set Successfully!**\n\n`{self.auto_reply_msg}`", parse_mode='Markdown')
            
        elif text == '.offreply':
            self.auto_reply_msg = None
            await event.reply("❌ **Auto Reply Turned OFF**\n\nI will not reply to DMs anymore.")
            
        elif text == '.check':
            current = self.auto_reply_msg or "❌ No auto reply set"
            await event.reply(f"📋 **Current Auto Reply:**\n\n`{current}`", parse_mode='Markdown')
            
        elif text == '.help':
            help_text = """
🤖 **Auto Reply UserBot Commands**

**.setreply <message>** - Set auto reply message
Example: `.setreply I'm offline right now. I'll reply later.`

**.offreply** - Turn off auto reply

**.check** - Check current auto reply

**.help** - Show this help

📢 **Support Channel:** @KIRA_BOTS
👥 **Support Group:** https://t.me/+qf33ETc6YDplYzk1

🔒 **Note:** Your data is secure and private.
            """
            await event.reply(help_text)
    
    async def stop(self):
        if self.client:
            await self.client.disconnect()
            self.is_running = False

class UserBotManager:
    def __init__(self):
        self.active_bots = {}
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        
    async def initialize(self):
        """Load existing users from database"""
        c = self.conn.cursor()
        c.execute("SELECT user_id, session_string FROM users WHERE status='active'")
        users = c.fetchall()
        
        for user_id, session_string in users:
            if len(self.active_bots) < MAX_USERS:
                await self.add_user(user_id, session_string)
                
    async def add_user(self, user_id, session_string):
        if len(self.active_bots) >= MAX_USERS:
            return False, "User limit reached"
            
        if user_id in self.active_bots:
            # Restart existing user
            await self.active_bots[user_id].stop()
            
        userbot = UserBot(session_string, user_id)
        self.active_bots[user_id] = userbot
        asyncio.create_task(userbot.start())
        
        return True, "UserBot started successfully"
        
    async def remove_user(self, user_id):
        if user_id in self.active_bots:
            await self.active_bots[user_id].stop()
            del self.active_bots[user_id]
            
    def get_active_count(self):
        return len(self.active_bots)

# Global instance
userbot_manager = UserBotManager()

async def start_manager():
    await userbot_manager.initialize()
    logger.info(f"UserBot Manager started with {userbot_manager.get_active_count()} active users")

if __name__ == "__main__":
    asyncio.run(start_manager())
