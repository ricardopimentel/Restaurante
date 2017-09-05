from django.conf.urls import url
from restaurante.acesso import views

urlpatterns = [
    url(r'^login/$', views.Login, name='Login'),
    url(r'^logout/$', views.Logout, name='Logout'),
]