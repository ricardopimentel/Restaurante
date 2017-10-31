from django.db import models

# Create your models here.
class config(models.Model):
    dominio = models.CharField(max_length=200)
    endservidor = models.CharField(max_length=200)
    gadmin = models.CharField(max_length=200)
    ou = models.CharField(max_length=200)
    filter = models.TextField('Filtro')
    hora_fechamento_vendas = models.TimeField('Horário do Fechamento das Vendas', default='23:59:59')