# Generated by Django 2.1.1 on 2018-09-19 14:21

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bairro',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Endereco',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('complemento', models.CharField(blank=True, max_length=200)),
                ('numero', models.PositiveIntegerField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Evento',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
                ('descricao', models.TextField()),
                ('banner', models.FilePathField()),
                ('data_cadastro', models.DateTimeField()),
                ('data_inicio', models.DateTimeField()),
                ('data_fim', models.DateTimeField()),
                ('id_categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Categoria')),
                ('id_endereco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Endereco')),
            ],
        ),
        migrations.CreateModel(
            name='Logradouro',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
                ('id_bairro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Bairro')),
            ],
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
                ('id_estado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Estado')),
            ],
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('cpf', models.PositiveIntegerField()),
                ('data_nasc', models.DateField(verbose_name='Data de Nascimento')),
                ('genero', models.CharField(choices=[('M', 'Masculino'), ('F', 'Feminino')], max_length=5)),
                ('id_endereco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Endereco')),
            ],
            options={
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
                'abstract': False,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='evento',
            name='id_promotor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Usuario'),
        ),
        migrations.AddField(
            model_name='endereco',
            name='id_logradouro',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Logradouro'),
        ),
        migrations.AddField(
            model_name='bairro',
            name='id_municipio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='E_Vento.Municipio'),
        ),
    ]
