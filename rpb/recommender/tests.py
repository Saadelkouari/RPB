from unittest import result
from urllib.request import Request
from django.test import TestCase
from .views import *
from .models import *
from django.http import HttpRequest
from django.test import Client
class TestingViewsFunctions(TestCase):
    def test_session_id_generator(self):        
        self.assertEqual(len(generate_session_id(User.objects.first())),64)

    def test1_is_authenticated(self):
        rq=Request(url='http://localhost:8080')
        rq.headers={"session-id":'something whichs false.'}
        self.assertEqual(is_authenticated(rq),None)
    
    def test2_is_authenticated(self):
        rq=Request(url='http://localhost:8080')
        user=User.objects.first()
        new_session_id=generate_session_id(user)
        user.session=Session(session_id=new_session_id)
        user.save()
        rq.headers={"session-id":new_session_id}
        self.assertEqual(is_authenticated(rq),User.objects.first())
    def test_cluster_fit(self):

        self.assertTrue(Cluster.fit())
    
    def test_cluster_predict(self):
        label=Cluster.label(User.objects.first())[0]
        self.assertTrue(isinstance(label,np.int32))

    def test_train(self):
        self.assertTrue(train())
    
    def test_predict(self):
        user=User.objects.first()
        predictions=predict(user)
        self.assertTrue((isinstance(predictions,QuerySet) and len(predictions)==4))
    
    def test_search_books(self):
        result=search_books("why things don't fall")
        self.assertTrue(isinstance(result,list))

    def test_save_books(self):
        rating={"id":"1362580","query":"why things don't fall"}
        self.assertEqual(save_books(rating),Book.objects.get(ID=rating['id']))
    
    def test_delete_update_rating(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.post('/api/user/read',{'id':'1362580','rating':-1,'query':"why things don't fall"})
        self.assertEqual(response.getvalue(),b'rating deleted')   
    
    
    def test_insert_update_rating(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.post('/api/user/read',{'id':'1362580','rating':4,'query':"why things don't fall"})
        self.assertEqual(response.getvalue(),b'rating added')
    
    def test_update_rating(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.post('/api/user/read',{'id':'1362580','rating':3,'query':"why things don't fall"})
        self.assertEqual(response.getvalue(),b'rating updated')

    def test_getBooks(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.get('/api/books')
        self.assertTrue(response.getvalue())
    
    def test_getMostRead(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.get('/api/mostread')
        self.assertTrue(response.getvalue())

    def test_getUser(self):
        user=User.objects.first()
        user.session=Session(session_id=generate_session_id(user))
        user.save()
        client=Client(HTTP_SESSION_ID=user.session.session_id)
        response=client.get('/api/user')
        self.assertTrue(response.getvalue())