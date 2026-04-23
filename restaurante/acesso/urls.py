from django.urls import re_path
from restaurante.acesso import views

urlpatterns = [
    re_path(r'^login/$', views.Login, name='Login'),
    re_path(r'^logout/$', views.Logout, name='Logout'),
    re_path(r'^trocar-dashboard/$', views.TrocarDashboard, name='TrocarDashboard'),
    re_path(r'^trocar-perfil/(?P<perfil_type>\w+)/$', views.TrocarPerfil, name='TrocarPerfil'),
]