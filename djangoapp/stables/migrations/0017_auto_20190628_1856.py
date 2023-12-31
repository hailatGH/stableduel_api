# Generated by Django 2.0.9 on 2019-06-28 18:56

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0016_auto_20190627_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='runner',
            name='career_stats',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='runner',
            name='past_performance',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='runner',
            name='pedigree',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[]),
        ),
        migrations.AddField(
            model_name='runner',
            name='workouts',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[]),
        ),
    ]
