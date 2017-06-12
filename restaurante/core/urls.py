# -*- coding: utf-8 -*-
from django.conf.urls import url
from restaurante.core import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^login/$', views.home),
    url(r'^logout/$', views.logout),
    url(r'^geraticket/$', views.geraticket),
    url(r'^venda/(?P<idaluno>.+)/(?P<idticket>.+)/(?P<idprato>.+)$', views.vender),
    url(r'^relatorios/$', views.relatorios),
    url(r'^relatoriovendas/$', views.relatoriovendas),
    url(r'^pdfvendas/$', views.pdfvendas),
    url(r'^relatorioticketsdia/$', views.relatorioticketsdia),
]
