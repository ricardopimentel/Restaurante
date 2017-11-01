from django.conf.urls import url
from restaurante.venda import views

urlpatterns = [
    url(r'^$', views.Venda, name='Venda'),
    url(r'^vender/(?P<id_pessoa>.+)$', views.Vender, name='Vender'),
]