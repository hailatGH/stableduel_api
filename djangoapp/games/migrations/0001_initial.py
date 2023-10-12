# Generated by Django 2.0.9 on 2019-05-01 15:10

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('racecards', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('params', django.contrib.postgres.fields.jsonb.JSONField(default={})),
                ('name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('racecards', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='racecards.Racecard')),
            ],
        ),
    ]
