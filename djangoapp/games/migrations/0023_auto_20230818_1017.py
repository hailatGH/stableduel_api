# Generated by Django 2.0.9 on 2023-08-18 10:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0022_auto_20230816_1402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamepayout',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Payout'),
        ),
    ]
