# Generated by Django 2.0 on 2022-09-02 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_delete_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrador',
            name='id_pessoa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.pessoa'),
        ),
        migrations.AlterField(
            model_name='aluno',
            name='id_pessoa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.pessoa'),
        ),
        migrations.AlterField(
            model_name='pessoa',
            name='usuario',
            field=models.CharField(max_length=18, unique=True),
        ),
        migrations.AlterField(
            model_name='prato',
            name='descricao',
            field=models.CharField(max_length=200, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='prato',
            name='preco',
            field=models.FloatField(verbose_name='Preço'),
        ),
        migrations.AlterField(
            model_name='prato',
            name='status',
            field=models.BooleanField(default=True, verbose_name='Ativo?'),
        ),
        migrations.AlterField(
            model_name='usuariorestaurante',
            name='id_pessoa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.pessoa'),
        ),
        migrations.AlterField(
            model_name='venda',
            name='id_aluno',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.aluno'),
        ),
        migrations.AlterField(
            model_name='venda',
            name='id_prato',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.prato'),
        ),
        migrations.AlterField(
            model_name='venda',
            name='id_usuario_restaurante',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.usuariorestaurante'),
        ),
    ]
