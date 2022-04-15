from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.models import User
from mongoengine import connect, ValidationError
from .models import User,Session
from datetime import datetime
import secrets
from blake3 import blake3
# Create your views here.
connect(db='rpb_db')

def getUser(request):
    if request.method == 'GET': 
        session_id = request.headers['session-id']
        print(session_id)
        try:
            session=Session.objects.get(session_id=session_id)
            user=session.user
            print(session.user)
            user.password =''
            return HttpResponse(user.to_json(),status=200)
        except Exception as e:
            print(e)
            return HttpResponse(e,status=400)





def LoginView(request):
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user=User.objects.get(username=username,password=password)
            try:
                past_session=Session.objects.get(user=user.id)
                past_session.delete()
            except Session.DoesNotExist:
                True
            session_id=blake3(user.username.encode('utf-8')+user.password.encode('utf-8')+datetime.now().strftime("%m/%d/%Y--%H:%M:%S").encode('utf-8')).hexdigest()
            new_session=Session(user=user.id,session_id=session_id)
            new_session.save()
            return HttpResponse(new_session.to_json(),status=200)
        except Exception as e:
            print(e)
            return HttpResponse(e,status=400)

def RegisterView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        try:
            user = User(username=username, password=password, email=email)
            user.save()
            session_id=blake3(user.username.encode('utf-8')+user.password.encode('utf-8')+datetime.now().strftime("%m/%d/%Y--%H:%M:%S").encode('utf-8')).hexdigest()
            new_session=Session(user=user.id,session_id=session_id)
            new_session.save()
            return HttpResponse(new_session.to_json(),status=200)
        except  ValidationError as e:
            print(e)
            return HttpResponse(e,status=400)
