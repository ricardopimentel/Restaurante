from django.conf.urls import url
from restaurante.administracao import views

urlpatterns = [
    url(r'^$', views.Administracao, name='Administracao'),
    url(r'^activedirectory/$', views.Dados_ad, name='ConfigAD'),
    url(r'^configuracaoinicial/$', views.ConfigInicial, name='ConfigInicial'),
    url(r'^cadastroprato/$', views.CadastroPrato, name='CadastroPrato'),
    url(r'^excluirpratos/$', views.ExcluirPratos, name='ExcluirPratos'),
    url(r'^editarpratos/(?P<id_prato>.+)$', views.EditarPrato, name='EditarPrato'),
    url(r'^horariolimitevendas/$', views.HorarioLimiteVendas, name='HorarioLimiteVendas'),
    url(r'^tutoriais/(?P<action>.+)$', views.Tutoriais, name='Tutoriais'),
    url(r'^configuracao/$', views.Configuracao, name='Configuracao'),
    url(r'^cadastrobolsistas/$', views.CadastroBolsistas, name='CadastroBolsistas'),
    url(r'^excluirbolsistas/$', views.ExcluirBolsistas, name='ExcluirBolsistas'),
]