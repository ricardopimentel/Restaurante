# Generated by Django 4.2.2 on 2024-11-19 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voucher', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='liberacao',
            old_name='voucher',
            new_name='id_voucher',
        ),
    ]
