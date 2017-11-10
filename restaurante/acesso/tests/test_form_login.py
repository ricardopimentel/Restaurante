from django.test import TestCase
from django.shortcuts import resolve_url as r

from restaurante.acesso.forms import LoginForm
from restaurante.administracao.models import config


class FormLoginTest(TestCase):
    def setUp(self):
        config.objects.create(
            id=1,
            dominio='dominio',
            endservidor='endservidor',
            gadmin='gadmin',
            ou='ou',
            filter='filter'
        )
        self.response = self.client.get(r('Login'))
        self.form = LoginForm(self.response.wsgi_request)
        self.expected = ['usuario', 'senha',]


    def test_form(self):
        """O formulario deve ter dois campos usuario e senha"""
        self.assertSequenceEqual(self.expected, list(self.form.fields))


