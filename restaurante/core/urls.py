# -*- coding: utf-8 -*-
from django.conf.urls import url
from restaurante.core import views

urlpatterns = [
    url(r'^$', views.Home, name='Home'),
    url(r'^login/$', views.Home, name='Login'),
    url(r'^logout/$', views.Logout, name='Logout'),
    url(r'^venda/$', views.Venda, name='Venda'),
    url(r'^vender/(?P<id_pessoa>.+)$', views.Vender, name='Vender'),
]
