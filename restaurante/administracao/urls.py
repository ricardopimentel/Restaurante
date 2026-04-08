from django.urls import re_path
from restaurante.administracao import views

urlpatterns = [
    re_path(r'^$', views.Administracao, name='Administracao'),
    re_path(r'^activedirectory/$', views.Dados_ad, name='ConfigAD'),
    re_path(r'^configuracaoinicial/$', views.ConfigInicial, name='ConfigInicial'),
    re_path(r'^cadastroprato/$', views.CadastroPrato, name='CadastroPrato'),
    re_path(r'^excluirpratos/$', views.ExcluirPratos, name='ExcluirPratos'),
    re_path(r'^editarpratos/(?P<id_prato>.+)$', views.EditarPrato, name='EditarPrato'),
    re_path(r'^horariolimitevendas/$', views.HorarioLimiteVendas, name='HorarioLimiteVendas'),
    re_path(r'^tutoriais/(?P<action>.+)$', views.Tutoriais, name='Tutoriais'),
    re_path(r'^configuracao/$', views.Configuracao, name='Configuracao'),
    re_path(r'^cadastrobolsistas/$', views.CadastroBolsistas, name='CadastroBolsistas'),
    re_path(r'^excluirbolsistas/$', views.ExcluirBolsistas, name='ExcluirBolsistas'),
    re_path(r'^cadastrocolaboradores/$', views.CadastroColaboradores, name='CadastroColaboradores'),
    re_path(r'^excluircolaboradores/$', views.ExcluirColaboradores, name='ExcluirColaboradores'),
    re_path(r'^configuracao/pix/$', views.ConfigPix, name='ConfigPix'),
    re_path(r'^cardapio/$', views.GerenciarCardapio, name='GerenciarCardapio'),
    re_path(r'^cardapio/opcoes/$', views.GerenciarOpcoesAlimento, name='GerenciarOpcoesAlimento'),
    re_path(r'^cardapio/opcoes/remover/(?P<id_opcao>.+)$', views.RemoverOpcaoAlimento, name='RemoverOpcaoAlimento'),
    re_path(r'^cardapio/opcoes/importar/$', views.ImportarOpcoesJSON, name='ImportarOpcoesJSON'),
    re_path(r'^cardapio/opcoes/exportar/$', views.ExportarOpcoesJSON, name='ExportarOpcoesJSON'),
]