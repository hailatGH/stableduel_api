# Generated by Django 2.0.9 on 2023-08-16 14:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0021_gamepayout'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamepayout',
            name='position',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Finish Position'),
        ),
        migrations.AlterField(
            model_name='gamepayout',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Payout'),
        ),
    ]
