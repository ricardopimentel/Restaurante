from django.test import TestCase
from django.shortcuts import resolve_url as r

from restaurante.administracao.models import config


class ViewLoginTest(TestCase):
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


    def test_get(self):
        """GET / must return code 200"""
        self.assertEqual(200, self.response.status_code)


