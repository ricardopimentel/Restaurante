from django.urls import re_path
from restaurante.voucher import views

urlpatterns = [
    re_path(r'^$', views.GeraLiberacao, name='Voucher'),
    re_path(r'^geraliberacao/$', views.GeraLiberacao, name='GeraLiberacao'),
    re_path(r'^cadastrovouchers/$', views.CadastroVouchers, name='CadastroVouchers'),
    re_path(r'^excluirvouchers/$', views.ExcluirVouchers, name='ExcluirVouchers'),
]