import re
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.urls import reverse
from mongoengine import connect, ValidationError
from .models import *
from datetime import datetime
import secrets
import json
from lightfm import LightFM
from lightfm.data import Dataset
from blake3 import blake3
import numpy as np
from bson.json_util import dumps, loads
import random
from libgen_api import LibgenSearch
from bs4 import BeautifulSoup
import requests
from collections import ChainMap
from bson.objectid import ObjectId
# Create your views here.
connect(db='rpb_d')

def train():
    data=Dataset()
    model=LightFM() 
    books_c=Book.objects.aggregate([{"$project":{"_id":1}}])
    users_c=User.objects.aggregate([{"$project":{"_id":1}}])
    books=[str(b['_id']) for b in list(books_c)]
    users=[str(u['_id']) for u in list(users_c)]

    data.fit(users,books)
    interactions_pipeline=[{"$unwind":"$ratings"},{"$project":{"ratings.ID" : 1,"ratings.rating" : 1}}]
    interactions_c=User.objects.aggregate(interactions_pipeline)
    interactions=[]
    for elm in list(interactions_c):
        temp=[]
        temp.append(str(list(elm.values())[0]))
        temp.append(str(list(list(elm.values())[1].values())[0]))
        temp.append(float(list(list(elm.values())[1].values())[1]))    
        interactions.append(temp)
    mappings=Mapping.objects.first()
    dt=datetime.today()
    date=mappings.date
    if date is None: 
        mappings.date=datetime.utcnow()
        mappings.times_used=1 
    elif date.day!=dt.day or date.month!=dt.month or date.year!=dt.year:
        mappings.times_used=1
    else: mappings.times_used+=1
    (interactions,weights)=data.build_interactions(interactions)
    mappings.user_mapping,r,mappings.book_mapping,q,=data.mapping()
    mappings.save()
    model.fit(interactions,sample_weight=weights)
    return data,model

    
def predict(user):
    data,model=train()
    mappings=Mapping.objects.first()
    userid=mappings.user_mapping[str(user.id)]
    books=list(mappings.book_mapping.values())
    interactions_pipeline=[{"$unwind":"$ratings"},{"$project":{"ratings.ID" : 1,"ratings.rating" : 1}}]
    interactions_c=User.objects.aggregate(interactions_pipeline)
    books_already=[]
    for elm in list(interactions_c):
        books_already.append(str(list(list(elm.values())[1].values())[0]))
    books_to_predict=[b for b in books if b not in books_already]
    predictions=model.predict(userid,books_to_predict)
    indxs = np.argpartition(predictions, -4)[-4:]
    pred_books=[ ObjectId(list(mappings.book_mapping.keys())[list(mappings.book_mapping.values()).index(ind)]) for ind in indxs]
    result_books=Book.objects.filter(__raw__={"_id":{"$in":pred_books}})
    return result_books
    
def search_books(name,id=None):
    s = LibgenSearch()
    if id is None:
        results=s.search_title(name)[:5]
        for r in results:
            r['query']=name
            page = requests.get(r['Mirror_1'])
            soup = BeautifulSoup(page.content, 'html.parser')
            img=soup.findAll('img')[0].get('src')
            r['image']="http://library.lol/"+img
        return results
    r=s.search_title_filtered(name,{"ID":id})[0]
    r['query']=name
    page = requests.get(r['Mirror_1'])
    soup = BeautifulSoup(page.content, 'html.parser')
    img=soup.findAll('img')[0].get('src')
    r['image']="http://library.lol/"+img
    return r

def printreq(req):
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' ,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))



def save_books(rating):
    try:
        book=Book.objects.get(__raw__={"ID":rating["id"]})
        return book
    except Exception as e:
        print(e)
        book_dict=search_books(rating['query'],rating['id'])
        for key in [key for key in book_dict.keys() if key not in [k for k,v in Book._fields.items()]]: book_dict.pop(key)
        book_dict['query']=rating['query']
        book=Book.from_json(dumps(book_dict))
        book.save()
        book.reload()
        return book




def is_authenticated(request):
    try:
        session_id = request.headers['session-id']
        user=User.objects.get(__raw__={'session.session_id':session_id})
        if (user.session.expires > datetime.utcnow()): return user
        else: return None
    except Exception as e:
        print(e)
        return None



def update_rating(request):
    if request.method == 'POST':
        user=is_authenticated(request)
        book=request.POST.get('id')
        rating=request.POST.get('rating')
        if user==None: return HttpResponse("session timed out.",status=440)
        if user and book and rating:
            book=save_books(request.POST)
            if bool(list(User.objects.aggregate([{"$match":{"session.session_id":user.session.session_id}},{'$unwind':'$ratings'},{"$match":{"ratings.ID":book.id}}]))):
                for r in user.ratings:
                    if r.ID.id==book.id:
                        if rating=='-1': 
                            user.ratings.remove(r)
                            message='rating deleted'
                        else: 
                            r.rating=rating
                            message='rating updated'
                user.save()
                return HttpResponse(message,status=200)
            else:
                user.ratings.append(Rating.from_json(dumps({'ID':book.id,'rating':float(rating)})))
                user.save()
            return HttpResponse("rating added",status=200)
        return HttpResponse("Book wasn't added to user rating.",status=400)

def get_times_suggestions_used(request):
    if request.method == 'GET':
        mapping=Mapping.objects.first()
        return HttpResponse(dumps({"times":mapping.times_used}),status=200)

def remove_rating(request):
    if request.method == 'POST':
        user=is_authenticated(request)
        book=request.POST.get('id')
        if user==None: return HttpResponse("Session timed out.",status=440)
        if book:

            return HttpResponse("Book removed from user ratings",status=200)


def getBooks(request):
    if request.method == 'GET':
        user=is_authenticated(request)
        if user is None: return HttpResponse('session expired',status=440)
        ratings=user.ratings
        books=[book.ID.to_mongo().to_dict() for book in ratings]
        for book,r in zip(books,ratings):
            book['rating']=str(r.rating)
        return HttpResponse(dumps(books),status=200)

def getMostRead(request):
    if request.method == 'GET':
        interactions_pipeline=[{"$unwind":"$ratings"},{"$group":{"_id" : "$ratings.ID","count":{"$sum":1}}}, { "$project": { "_id": 1, "count":1} }]
        rbooks=list(User.objects.aggregate(interactions_pipeline))
        rbooks.sort(key=lambda x: x["_id"])
        books_id=[book["_id"] for book in rbooks]
        counts=[book["count"] for book in rbooks]
        books=[b.to_mongo().to_dict() for b in Book.objects.filter(__raw__={"_id":{"$in":books_id}})]
        books.sort(key=lambda x: x["_id"])
        for bookz,countz in zip(books,counts):
            bookz['count']=countz
        books.sort(reverse=True,key=lambda book:book["count"])
        return HttpResponse(dumps(list(books)),status=200)

def getUser(request):
    if request.method == 'GET':
        user=is_authenticated(request)
        try:
            if user is None: return HttpResponse('session expired',status=440)
            user.password =''
            return HttpResponse(user.to_json(),status=200)
        except Exception as e:
            print(e)
            return HttpResponse(e,status=400)
    if request.method == 'POST':
        user=is_authenticated(request)
        if user is None: return HttpResponse('session expired',status=440)
        else:
            for key in User._fields.keys():
                if request.POST.get(key) is not None:
                    user[key]=request.POST[key]
            try:
                user.save()
                return HttpResponse("Profile updated",status=200)
            except Exception as e:
                print(e)
                return HttpResponse(e,status=400)



def submit_form(request):
    if request.method == 'POST':
        user=is_authenticated(request)
        if user is None: return HttpResponse('expired session',status=440)
        query=request.POST.get('query')
        if query:
            return HttpResponse(json.dumps(search_books(query)),status=200)

def get_suggestions(request):
    if request.method == 'GET':
        user=is_authenticated(request)
        if user is None: return HttpResponse('session expired',status=440)
        predictions=predict(user)
        return HttpResponse(dumps([p.to_mongo().to_dict() for p in predictions]),status=200)

def LoginView(request):
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user=User.objects.get( __raw__= {'username':username,'password':password} )
            session_id=blake3(user.username.encode('utf-8')+user.password.encode('utf-8')+datetime.now().strftime("%m/%d/%Y--%H:%M:%S").encode('utf-8')).hexdigest()
            user.session=Session(session_id=session_id)
            user.birthday=datetime.now()
            user.save()
            return HttpResponse(user.session.to_json(),status=200)
        except Exception as e:
            print(e)
            return HttpResponse(e,status=400)

def RegisterView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birthday = datetime.strptime(request.POST.get('birthday'),'%Y-%M-%d')
        sexe=request.POST.get('sexe')
        genres=request.POST.get('genres')
        try:
            user = User(username=username, password=password,email=email,birthday=birthday,sexe=sexe,genres=genres)
            session_id=blake3(user.username.encode('utf-8')+user.password.encode('utf-8')+datetime.now().strftime("%m/%d/%Y--%H:%M:%S").encode('utf-8')).hexdigest()
            user.session=Session(session_id=session_id)
            user.save()
            return HttpResponse(user.session.to_json(),status=200)
        except  Exception as e:
            print(e)
            return HttpResponse(e,status=400)
