# Generated by Django 2.0.9 on 2020-06-26 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0023_stable_entry_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='stable',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
