from django.conf.urls import url
from restaurante.administracao import views

urlpatterns = [
    url(r'^$', views.Administracao, name='Administracao'),
    url(r'^activedirectory/$', views.Dados_ad, name='ConfigAD'),
    url(r'^configuracaoinicial/$', views.ConfigInicial, name='ConfigInicial'),
]