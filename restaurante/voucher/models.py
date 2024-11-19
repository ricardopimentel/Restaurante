from django.db import models

# Create your models here.
class voucher (models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return self.codigo


class liberacao (models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=14)
    id_voucher = models.ForeignKey(voucher, on_delete=models.PROTECT)


    def __str__(self):
        return self.id_voucher.codigo