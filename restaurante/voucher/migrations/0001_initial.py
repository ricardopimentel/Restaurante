# Generated by Django 4.2.2 on 2024-11-12 16:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='voucher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20)),
                ('usado', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='liberacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('telefone', models.CharField(max_length=11)),
                ('voucher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='voucher.voucher')),
            ],
        ),
    ]
