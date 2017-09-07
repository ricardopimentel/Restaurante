# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-05 17:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='config',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dominio', models.CharField(max_length=200)),
                ('endservidor', models.CharField(max_length=200)),
                ('gadmin', models.CharField(max_length=200)),
                ('ou', models.CharField(max_length=200)),
                ('filter', models.TextField(verbose_name='Filtro')),
                ('hora_fechamento_vendas', models.TimeField(default='23:59:59')),
            ],
        ),
    ]