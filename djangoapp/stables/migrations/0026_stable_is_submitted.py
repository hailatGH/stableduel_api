# Generated by Django 2.0.9 on 2021-01-11 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0025_remove_stable_deleted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='stable',
            name='is_submitted',
            field=models.BooleanField(default=False),
        ),
    ]
