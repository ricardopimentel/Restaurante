from django.db import models
from restaurante.core.models import aluno
import uuid

class TicketAluno(models.Model):
    id_aluno = models.ForeignKey(aluno, on_delete=models.PROTECT)
    data_compra = models.DateTimeField(auto_now_add=True)
    valor = models.FloatField('Valor Pago')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pago = models.BooleanField('Pago?', default=False)
    usado = models.BooleanField('Usado?', default=False)
    tipo_refeicao = models.CharField('Tipo de Refeição', max_length=15, default='Almoço')
    data_utilizacao = models.DateTimeField('Data de Uso', null=True, blank=True)
    data_pagamento = models.DateTimeField('Data do Pagamento', null=True, blank=True)
    id_pagamento_externo = models.CharField('ID Pagamento Externo', max_length=100, null=True, blank=True)
    pix_copia_e_cola = models.TextField('PIX Copia e Cola', null=True, blank=True)
    pix_qr_code_base64 = models.TextField('PIX QR Code Base64', null=True, blank=True)

    def __str__(self):
        return f"{self.id_aluno} - {self.data_compra} ({'Pago' if self.pago else 'Pendente'})"
