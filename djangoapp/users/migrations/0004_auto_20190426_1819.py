# Generated by Django 2.0.9 on 2019-04-26 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20190426_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='stable_name',
            field=models.CharField(help_text='Name of the users stable', max_length=50, unique=True),
        ),
    ]
