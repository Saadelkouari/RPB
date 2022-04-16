from datetime import datetime, timedelta
from mongoengine import *
# Create your models here.

class Session(EmbeddedDocument):
    session_id=StringField(max_length=255, unique=True,required=True)
    expires=DateTimeField(default=datetime.utcnow()+timedelta(days=1))


class User(Document):
    username=StringField(max_length=255,min_length=3,required=True,unique=True)
    password=StringField(max_length=255,min_length=8,required=True)
    email=EmailField(unique=True,required=True)
    first_name=StringField(max_length=255)
    last_name=StringField(max_length=255)
    session=EmbeddedDocumentField(Session,unique=True)


