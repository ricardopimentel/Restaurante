from django.conf.urls import url
from restaurante.core import views

urlpatterns = [
    url(r'^$', views.Home, name='Home'),
    url(r'^login/$', views.Home, name='Login'),
]
