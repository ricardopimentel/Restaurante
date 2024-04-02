from django.urls import re_path
from restaurante.core import views

urlpatterns = [
    re_path(r'^$', views.Home, name='Home'),
    re_path(r'^login/$', views.Home, name='Login'),
]
