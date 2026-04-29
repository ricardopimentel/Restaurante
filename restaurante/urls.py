"""restaurante URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include
from django.urls import re_path
from django.views.generic import TemplateView

urlpatterns = [
    re_path(r'^restaurante/manifest.json$', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest.json'),
    re_path(r'^restaurante/sw.js$', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),
    
    re_path(r'^restaurante/', include('restaurante.core.urls')),
    re_path(r'^restaurante/relatorios/', include('restaurante.relatorios.urls')),
    re_path(r'^restaurante/acesso/', include('restaurante.acesso.urls')),
    re_path(r'^restaurante/administracao/', include('restaurante.administracao.urls')),
    re_path(r'^restaurante/venda/', include('restaurante.venda.urls')),
    re_path(r'^restaurante/voucher/', include('restaurante.voucher.urls')),
    re_path(r'^restaurante/estudante/', include('restaurante.ticket_estudante.urls')),
]
