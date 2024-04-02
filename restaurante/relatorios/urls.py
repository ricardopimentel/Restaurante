# -*- coding: utf-8 -*-
from django.urls import re_path

from restaurante.relatorios import views

urlpatterns = [
    re_path(r'^$', views.Relatorios, name='Relatorios'),
    re_path(r'^relatoriovendas/$', views.RelatorioVendas, name='RelatorioVendas'),
    re_path(r'^relatoriocustoalunoperiodo/$', views.RelatorioCustoAlunoPeriodo, name='RelatorioCustoAlunoPeriodo'),
    re_path(r'^pdfvendas/$', views.PdfVendas, name='PdfVendas'),
    re_path(r'^pdfcustoalunoperiodo/$', views.PdfCustoAlunoPeriodo, name='PdfCustoAlunoPeriodo'),
]