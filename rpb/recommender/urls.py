from django.urls import path
from . import views

urlpatterns =[

    path('register',views.RegisterView),
    path('login',views.LoginView),
    path('user',views.getUser),
    path('search',views.submit_form),
    path('user/read',views.update_rating),
    path('books',views.getBooks),
    path('mostread',views.getMostRead),
    path('user/suggestions',views.get_suggestions),
    path('times_used',views.get_times_suggestions_used),
]