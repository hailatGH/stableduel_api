# Generated by Django 2.0.9 on 2020-06-15 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0011_auto_20200528_1258'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='pool',
        ),
        migrations.AlterField(
            model_name='game',
            name='contest_amount',
            field=models.IntegerField(default=0, verbose_name='Guaranteed Pool'),
        ),
        migrations.AlterField(
            model_name='game',
            name='winner_limit',
            field=models.IntegerField(default=1, verbose_name='Players Paid'),
        ),
    ]
