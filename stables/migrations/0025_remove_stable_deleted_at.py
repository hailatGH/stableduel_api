# Generated by Django 2.0.9 on 2020-07-01 14:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0024_stable_deleted_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stable',
            name='deleted_at',
        ),
    ]