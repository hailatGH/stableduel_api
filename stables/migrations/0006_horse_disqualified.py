# Generated by Django 2.0.9 on 2019-05-29 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0005_auto_20190522_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='horse',
            name='disqualified',
            field=models.BooleanField(default=False),
        ),
    ]