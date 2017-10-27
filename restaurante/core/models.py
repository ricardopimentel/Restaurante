from __future__ import unicode_literals

from django.db import models

# Create your models here.
class pessoa (models.Model):
    nome = models.CharField(max_length=100)
    usuario = models.CharField(max_length=11, unique=True)
    status = models.BooleanField()


    def __str__(self):
        return str(self.nome)


class administrador (models.Model):
    id_pessoa = models.ForeignKey(pessoa)


    def __str__(self):
        return str(pessoa.nome)


class usuariorestaurante (models.Model):
    id_pessoa = models.ForeignKey(pessoa)


    def __str__(self):
        return str(pessoa.nome)


class prato (models.Model):
    descricao = models.CharField('Descrição', max_length=200)
    preco = models.FloatField('Preço')
    status = models.BooleanField('Ativo?', default=True)


class aluno (models.Model):
    id_pessoa = models.ForeignKey(pessoa)


    def __str__(self):
        return str(pessoa.nome)


class venda (models.Model):
    data = models.DateTimeField()
    valor = models.FloatField()
    id_prato = models.ForeignKey(prato)
    id_usuario_restaurante = models.ForeignKey(usuariorestaurante)
    id_aluno = models.ForeignKey(aluno)