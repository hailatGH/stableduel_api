# Generated by Django 2.0.9 on 2020-04-09 01:03

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0020_runner_custom_stats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='runner',
            name='custom_stats',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None),
        ),
    ]
