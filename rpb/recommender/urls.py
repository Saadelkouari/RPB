from django.urls import path
from . import views

urlpatterns =[

    path('register',views.RegisterView),
    path('login',views.LoginView),
    path('user',views.getUser),

]