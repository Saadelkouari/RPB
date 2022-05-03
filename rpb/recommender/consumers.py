import json
from channels.generic.websocket import WebsocketConsumer
from .models import *
from asgiref.sync import async_to_sync
from .views import Cluster
from colorama import Fore

def is_authenticated(scope):
    try:
        session_id = dict(scope["headers"])[b"session-id"].decode("utf8")
        user=User.objects.get(__raw__={'session.session_id':session_id})
        if (user.session.expires > datetime.utcnow()): return user
        else: return None
    except Exception as e:
        print(e)
        return None

class ChatConsumer(WebsocketConsumer):
    def connect(self):

        user=is_authenticated(self.scope)
        if user is None: self.close()
        Cluster.fit()
        print("connecting to socket is the user",user)
        self.group_name=str(Cluster.label(user)[0])
        self.accept()
        messages=Chat.objects.get(__raw__={'chat_label':int(self.group_name)}).messages

        self.send(json.dumps({"chat_label":self.group_name,"messages":[{'sender':message.sender.username, 'message':message.value,'time':message.time.__str__()} for message in messages]}))
    def receive(self, text_data):
        event = json.loads(text_data)
        user=is_authenticated(self.scope)
        if user is None: self.close()
        else:
            message=event['message']
            chat_label=event['chat_label']
            chat=Chat.objects.get(__raw__={'chat_label':int(chat_label)})
            if chat is None: self.close()
            else:
                chat.messages.append(Message(value=message,sender=user.id))
                chat.save()
                return self.send_message(message)

    def send_message(self,message):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, {"type":"chat-message","message":message}
        )


    def fetch_messages(self, data):
        self.count = 0
        chat_label = data["chat_label"]
        messages = Chat.objects.get(__raw__={'label':chat_label}).messages
        content = {"messages":[m.to_mongo().to_dict() for m in messages]}
        self.send(json.dumps(content))


    def send_message(self, message):
        self.send(text_data=json.dumps(message))


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )