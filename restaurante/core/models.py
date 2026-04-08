from __future__ import unicode_literals

from django.db import models

# Create your models here.
class pessoa (models.Model):
    nome = models.CharField(max_length=100)
    usuario = models.CharField(max_length=20, unique=True)
    status = models.BooleanField()


    def __str__(self):
        return str(self.nome)


class administrador (models.Model):
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.PROTECT)


    def __str__(self):
        return str(pessoa.nome)


class usuariorestaurante (models.Model):
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.PROTECT)


    def __str__(self):
        return str(pessoa.nome)


class prato (models.Model):
    descricao = models.CharField('Descrição', max_length=200)
    preco = models.FloatField('Preço')
    preco_aluno = models.FloatField('Preço Aluno', default=0.0)
    status = models.BooleanField('Ativo?', default=True)


class aluno (models.Model):
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.PROTECT)


    def __str__(self):
        return str(pessoa.nome)


class venda (models.Model):
    data = models.DateTimeField()
    valor = models.FloatField()
    cem = models.BooleanField(default=False)
    id_prato = models.ForeignKey(prato, on_delete=models.PROTECT)
    id_usuario_restaurante = models.ForeignKey(usuariorestaurante, on_delete=models.PROTECT)
    id_aluno = models.ForeignKey(aluno, on_delete=models.PROTECT)


class alunoscem (models.Model):
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.PROTECT, unique=True)


class alunoscolaboradores (models.Model):
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.PROTECT, unique=True)


class CardapioDia(models.Model):
    TIPO_REFEICAO = (
        ('ALMOCO', 'Almoço'),
        ('JANTA', 'Janta'),
    )
    data = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO_REFEICAO)
    itens = models.TextField() # Armazenará os itens selecionados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('data', 'tipo')
        verbose_name = 'Cardápio do Dia'
        verbose_name_plural = 'Cardápios do Dia'

    def __str__(self):
        return f"{self.data} - {self.get_tipo_display()}"


class OpcaoAlimento(models.Model):
    CATEGORIAS = (
        ('Proteínas', 'Proteínas'),
        ('Acompanhamentos', 'Acompanhamentos'),
        ('Saladas', 'Saladas'),
        ('Sobremesas', 'Sobremesas'),
        ('Bebidas/Sucos', 'Bebidas/Sucos'),
    )
    nome = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS)

    class Meta:
        verbose_name = 'Opção de Alimento'
        verbose_name_plural = 'Opções de Alimentos'
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.categoria})"