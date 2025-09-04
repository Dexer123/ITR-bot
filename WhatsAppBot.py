from TelegramBot import TelegramBot

from whatsapp_api_client_python import API
from dotenv import load_dotenv
from datetime import datetime
from json import dumps
import mimetypes
import os



class WhatsAppBot:
    def __init__(self, id_instance: str=None, api_token: str=None, debug_mode: bool=False):
        load_dotenv()
        id_instance = id_instance or os.getenv("WA_ID_INSTANCE")
        api_token = api_token or os.getenv("WA_API_TOKEN")
        self.wa_group_id = os.getenv("WA_GROUP_ID")
        self.tg_bot = None

        if not id_instance or not api_token:
            raise ValueError("Не заданы ID_INSTANCE или API_TOKEN в .env")
        

        self.greenAPI = API.GreenAPI(
            id_instance, api_token,
            debug_mode=debug_mode
        )


    def start(self):
        self.greenAPI.webhooks.startReceivingNotifications(self.handler)
        
    def stop(self):
        self.greenAPI.webhooks.stopReceivingNotifications()
        self.tg_bot.send_group_message_sync("<Остановка бота>\n@dexering ⁉️🤨")
        
        
    def get_status_instance(self) -> None:
        status = self.greenAPI.account.getStatusInstance()
        state = self.greenAPI.account.getStateInstance()
        return f"Статус: {status.data['statusInstance']}\nСостояние: {state.data['stateInstance']}"
        
        
    def handler(self, type_webhook: str, body: dict, r=None) -> None:
        if type_webhook in ["incomingMessageReceived", "outgoingMessageReceived"]:
            r = self._incoming_message_received(body)
            if r:
                self.tg_bot.send_group_message_sync(r)


    @staticmethod
    def get_notification_time(timestamp: int) -> str:
        return str(datetime.fromtimestamp(timestamp))


    def _incoming_message_received(self, body: dict) -> str:
        if not self._is_valid_message(body):
            return
        
        sender_info = self._get_sender_info(body["senderData"])
        time = self.get_notification_time(body["timestamp"])
        msg_data = body["messageData"]
        msg_type = msg_data["typeMessage"]
        msg_text = self._extract_message_text(msg_data)
        
        if msg_type in ['textMessage', 'quotedMessage']:
            prefix = "Ответ на другое сообщение" if msg_type == 'quotedMessage' else "Сообщение"
            return f"{prefix} от {sender_info} в {time}: {msg_text}"
        
        
        if msg_type in ['imageMessage', 'videoMessage', 'documentMessage', 'audioMessage']:
            filename, url = self._get_file_info(msg_data.get("fileMessageData", {}), body)
            return f"Сообщение от {sender_info} в {time}: {msg_text}\n\nВложение: {filename}\nURL: {url}"
    
    def _is_valid_message(self, body: dict) -> bool:
        return (body["senderData"]["chatId"] == self.wa_group_id and 
                body["messageData"]["typeMessage"] not in ["deletedMessage", "revokedMessage"])
    
    def _get_sender_info(self, sender_data: dict) -> str:
        sender_num = sender_data["sender"].split("@", 1)[0]
        sender_name = f"({sender_data['senderName']})" if sender_data["senderName"] else ""
        return f"{sender_num}{sender_name}"
    
    def _extract_message_text(self, msg_data: dict) -> str:
        text = (msg_data.get("textMessageData", {}).get("textMessage", '') or 
                msg_data.get("fileMessageData", {}).get("caption", '') or
                msg_data.get("extendedTextMessageData", {}).get("text", ''))
        return text or "<Пустое сообщение>"
    
    def _get_file_info(self, file_data: dict, body: dict) -> tuple[str, str]:
        ext = mimetypes.guess_extension(file_data.get("mimeType", "").split(";")[0]) or ''
        filename = file_data.get("fileName", "").strip()
        
        if not filename or not filename.endswith(ext):
            filename = f"{filename or body['idMessage']}{ext}"
        
        url = (file_data.get("downloadUrl", '') or 
               self.greenAPI.receiving.downloadFile(body["senderData"]["chatId"], body["idMessage"]).get("downloadUrl", '') or
               "<URL не доступен>")
        
        return filename, url
    

if __name__ == "__main__":
    load_dotenv()

    id_instance = os.getenv("ID_INSTANCE")
    api_token = os.getenv("API_TOKEN")
    tg_token = os.getenv("TG_BOT_TOKEN")
    tg_group = os.getenv("TG_GROUP_CHAT_ID")
    tg_thread = os.getenv("TG_THREAD_ID")
    assert (id_instance and api_token and tg_token and tg_group), "Не заданы переменные окружения в .env"
    
    wa_bot = WhatsAppBot(id_instance, api_token)
    tg_bot = TelegramBot(parent=wa_bot, token=tg_token, group_chat_id=tg_group, thread_id=tg_thread)
    wa_bot.tg_bot = tg_bot
    tg_bot.run()
    
    wa_status = wa_bot.start()
    print("WA status:", wa_status)
    wa_bot.stop()
