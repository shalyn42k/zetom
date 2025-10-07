from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index_alias'),  # ← добавили
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('panel/', views.panel, name='panel'),
]
