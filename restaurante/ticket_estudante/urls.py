from django.urls import re_path
from restaurante.ticket_estudante import views

urlpatterns = [
    re_path(r'^$', views.HomeEstudante, name='HomeEstudante'),
    re_path(r'^meus-tickets/$', views.TicketsEstudante, name='TicketsEstudante'),
    re_path(r'^comprar/$', views.ComprarTicket, name='ComprarTicket'),
    re_path(r'^comprar/simular/$', views.SimularPagamento, name='SimularPagamento'), # Processa o PIX
    re_path(r'^pix/webhook/$', views.WebhookPix, name='WebhookPix'),
    re_path(r'^ticket/(?P<uuid>[0-9a-f-]+)/status/$', views.StatusTicket, name='StatusTicket'),
    re_path(r'^ticket/(?P<uuid>[0-9a-f-]+)/pagar/$', views.RevisarPagamento, name='RevisarPagamento'),
    re_path(r'^ticket/(?P<uuid>[0-9a-f-]+)/$', views.VisualizarTicket, name='VisualizarTicket'),
]
