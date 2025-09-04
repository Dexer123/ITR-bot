from telegram.ext import Application, MessageHandler, CommandHandler, filters
from dotenv import load_dotenv
from time import sleep
import telegram
import asyncio
import os

class TelegramBot:
    app: Application

    def __init__(self, parent=None, token=None, group_chat_id=None, thread_id=None, debug_mode: bool=False):
        load_dotenv()
        self.parent = parent
        self.debug_mode = debug_mode
        token = token or os.getenv("TG_BOT_TOKEN")
        self.group_chat_id = group_chat_id or os.getenv("TG_GROUP_CHAT_ID")
        self.thread_id = thread_id or os.getenv("TG_THREAD_ID")  # ID темы (message_thread_id)

        if not token:
            raise ValueError("Не задан TG_BOT_TOKEN в .env")

        self.app = Application.builder().token(token).build()
        
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        
        if self.debug_mode:
            self.app.add_handler(MessageHandler(filters.ALL, self.debug))

    async def send_group_message(self, message: str=None):
        if self.debug_mode:
            print("send_group_message:", message)
            return
            
        if not self.group_chat_id or not self.thread_id:
            raise ValueError("Не задан TG_GROUP_CHAT_ID или TG_THREAD_ID в .env")

        if message and not self.debug_mode:
            await self.app.bot.send_message(
                chat_id=int(self.group_chat_id),
                text=message,
                message_thread_id=int(self.thread_id)
            )
            
    def send_group_message_sync(self, message: str = None):
        asyncio.get_event_loop().run_until_complete(self.send_group_message(message))
        
        
    async def cmd_status(self, update, context):
        if not self.debug_mode:
            if self.parent:
                wa_status = self.parent.get_status_instance()
                await update.message.reply_text(f"📊 WhatsApp:\n{wa_status}")
            else:
                await update.message.reply_text("Нет связи с WhatsAppBot\n@dexering ⁉️🤨")
    
    async def debug(self, update, context):
        if update.message:
            print("chat_id:", update.message.chat_id)
            print("thread_id:", update.message.message_thread_id)
            print("text:", update.message.text)
        elif update:
            print(update)

            

    def run(self):
        while True:
            try:
                self.app.run_polling(drop_pending_updates=True)
            except telegram.error.NetworkError as e:
                print("Network error:", e)
                sleep(5)
            except Exception as e:
                print("Unexpected error:", e)
                sleep(5)
            
        


if __name__ == "__main__":
    tg_bot = TelegramBot(debug_mode=True)
    tg_bot.run()