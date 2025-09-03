from whatsapp_api_client_python import API
from dotenv import load_dotenv
from datetime import datetime
from json import dumps
import mimetypes
import os



class WhatsAppBot:
    def __init__(self, id_instance: str=None, api_token: str=None, debug_mode: bool=False):
        load_dotenv()
        id_instance = id_instance or os.getenv("ID_INSTANCE")
        api_token = api_token or os.getenv("API_TOKEN")

        if not id_instance or not api_token:
            raise ValueError("Не заданы ID_INSTANCE или API_TOKEN в .env")

        self.greenAPI = API.GreenAPI(
            id_instance, api_token,
            debug_mode=debug_mode
        )


    def start(self):
        # response = self.greenAPI.journals.lastIncomingMessages(120)
        # print(response.data)
        # return
        status = self.get_status_instance()
        print(status)
        self.greenAPI.webhooks.startReceivingNotifications(self.handler)
        return status
        
        
    def get_status_instance(self) -> None:
        status = self.greenAPI.account.getStatusInstance()
        return f"Статус: {status.data['statusInstance']}"
        
        
    def handler(self, type_webhook: str, body: dict, r=None) -> None:
        if type_webhook == "incomingMessageReceived":
            r = self._incoming_message_received(body)
        print(r)


    @staticmethod
    def get_notification_time(timestamp: int) -> str:
        return str(datetime.fromtimestamp(timestamp))


    def _incoming_message_received(self, body: dict) -> None:
        timestamp = body["timestamp"]
        time = self.get_notification_time(timestamp)

        data = dumps(body, ensure_ascii=False, indent=4)
        
        sender_num = body["senderData"]["sender"][:-4]
        sender = body["senderData"]["senderName"]
        sender_info = f"({sender})" if sender else ""
        chat_id = body["senderData"]["chatId"]
        if chat_id != "120363402111317806@g.us": # ИТР
            return  
        
        msg_type = body["messageData"]["typeMessage"]
        if msg_type not in ['imageMessage', 'videoMessage', 'documentMessage', 'audioMessage']:
            return f"Сообщение от {sender_num}{sender_info} в {time}: {data}\n\n"

        msg_id = body["idMessage"]
        file = body["messageData"].get("fileMessageData", {})
        url = file.get("downloadUrl", '') or self.greenAPI.receiving.downloadFile(chat_id, msg_id)
        filename = file.get("fileName", '')
        mimetype = file.get("mimetype", '')
        ext = mimetypes.guess_extension(mimetype.split(";")[0])
        if filename and ext and not filename.endswith(ext):
            filename += ext
        
        if not url or not filename:
            return
        
        return f"Сообщение от {sender_num}{sender_info} в {time}: {data}\nВложение: {filename}{filename}\n\n"
        
        
            

bot = WhatsAppBot(debug_mode=False)
bot.start()