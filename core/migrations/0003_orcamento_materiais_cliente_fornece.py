# Generated by Django 5.2.3 on 2025-07-11 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_cliente_cpf_cnpj_alter_cliente_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='materiais_cliente_fornece',
            field=models.BooleanField(default=False, verbose_name='Cliente fornece os materiais?'),
        ),
    ]
