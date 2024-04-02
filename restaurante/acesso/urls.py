from django.urls import re_path
from restaurante.acesso import views

urlpatterns = [
    re_path(r'^login/$', views.Login, name='Login'),
    re_path(r'^logout/$', views.Logout, name='Logout'),
]