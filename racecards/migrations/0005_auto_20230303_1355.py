# Generated by Django 2.0.9 on 2023-03-03 13:55

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('racecards', '0004_trackvideo'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackvideo',
            name='forceFormat',
            field=models.CharField(choices=[['ios', 'Ios'], ['rtsp', 'rstp'], ['auto', 'auto']], default='ios', max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='trackvideo',
            name='output',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='trackvideo',
            name='speed',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='trackvideo',
            name='staticspeed',
            field=models.IntegerField(choices=[[0, 'Adaptive'], [1, 'Single']], default=0, null=True),
        ),
        migrations.AddField(
            model_name='trackvideo',
            name='usr',
            field=models.CharField(blank=True, default=None, max_length=25, null=True),
        ),
    ]