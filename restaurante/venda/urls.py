from django.urls import re_path
from restaurante.venda import views

urlpatterns = [
    re_path(r'^$', views.Vendas, name='Vendas'),
    re_path(r'^venda/$', views.Venda, name='Venda'),
    re_path(r'^venda-lotes/$', views.VendaLotes, name='VendaEmLotes'),
    re_path(r'^vender-lotes/(?P<id_pessoa>.+)$', views.VenderLotes, name='VenderEmLotes'),
    re_path(r'^vender/(?P<id_pessoa>.+)$', views.Vender, name='Vender'),
]