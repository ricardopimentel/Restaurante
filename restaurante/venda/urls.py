from django.conf.urls import url
from restaurante.venda import views

urlpatterns = [
    url(r'^$', views.Vendas, name='Vendas'),
    url(r'^venda/$', views.Venda, name='Venda'),
    url(r'^venda-lotes/$', views.VendaLotes, name='VendaEmLotes'),
    url(r'^vender-lotes/(?P<id_pessoa>.+)$', views.VenderLotes, name='VenderEmLotes'),
    url(r'^vender/(?P<id_pessoa>.+)$', views.Vender, name='Vender'),
]