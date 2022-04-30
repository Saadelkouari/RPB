from datetime import datetime, timedelta
from mongoengine import *
from numpy import require
# Create your models here.

class Session(EmbeddedDocument):
    session_id=StringField(max_length=255, unique=True,required=True)
    expires=DateTimeField(default=datetime.utcnow()+timedelta(days=1))

class Book(Document):
    ID=StringField(max_length=255,required=True,unique=True)
    Title=StringField(max_length=255,required=True)
    Author=StringField(max_length=255,required=True)
    Year=StringField(max_length=4,required=True)
    cover=ImageField(required=True)
    query=StringField(max_length=255,required=True)
    image=StringField(max_length=255,required=True)

class Rating(EmbeddedDocument):
    ID=ReferenceField(Book,DBRef='ID',required=True)
    rating=DecimalField(max=5,min=0,required=True)

SEXES=(('M','MALE'),('F','FEMALE'))

class User(Document):
    username=StringField(max_length=255,min_length=3,required=True,unique=True)
    password=StringField(max_length=255,min_length=8,required=True)
    email=EmailField(unique=True,required=True)
    first_name=StringField(max_length=255)
    last_name=StringField(max_length=255)
    birthday=DateTimeField(required=True)
    session=EmbeddedDocumentField(Session,unique=True)
    ratings=ListField(EmbeddedDocumentField(Rating))
    sexe=StringField(max_length=1,choice=SEXES)
    genres=ListField()



class Mapping(Document):
    user_mapping=DictField()
    book_mapping=DictField()
