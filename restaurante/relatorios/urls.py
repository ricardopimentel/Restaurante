# -*- coding: utf-8 -*-
from django.conf.urls import url

from restaurante.relatorios import views

urlpatterns = [
    url(r'^$', views.Relatorios, name='Relatorios'),
    url(r'^relatoriovendas/$', views.RelatorioVendas, name='RelatorioVendas'),
    url(r'^pdfvendas/$', views.PdfVendas, name='PdfVendas'),
]