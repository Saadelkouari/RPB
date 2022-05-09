import json
from channels.generic.websocket import WebsocketConsumer
from .models import *
from asgiref.sync import async_to_sync
from .views import Cluster
from colorama import Fore

def is_authenticated(scope):
    try:
        session_id = scope["query_string"].decode("utf8")
        print(session_id[11:])
        user=User.objects.get(__raw__={'session.session_id':session_id[11:]})
        if (user.session.expires > datetime.utcnow()): return user
        else: return None
    except Exception as e:
        print(e)
        return None

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print("scope is :",dict(self.scope))
        user=is_authenticated(self.scope)
        if user is None: self.close()
        Cluster.fit()
        print("connecting to socket is the user",user)
        self.group_name=str(2)
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )
        print("chat label",self.group_name)
        messages=Chat.objects.get(__raw__={'chat_label':int(self.group_name)}).messages
        self.send(json.dumps({"chat_label":self.group_name,"messages":[{'sender':message.sender.username, 'message':message.value,'time':message.time.__str__()} for message in messages]}))
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )    
    
    def xo_message(self,message):
        print("somethigns 2")

        print("somethigns 3")
    def chat_message(self, event):
        self.send(text_data=json.dumps(event['message']))

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
                message=Message(value=message,sender=user.id)
                chat.messages.append(message)
                chat.save()
                print("seomthing")
                async_to_sync(self.channel_layer.group_send)(
                self.group_name, {"type":"chat_message","message":{"sender":message.sender.username,"message":message.value,"time":message.time.__str__()}}
        )    
    
    def _get_connection_id(self):
        return ''.join(e for e in self.channel_name if e.isalnum())

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