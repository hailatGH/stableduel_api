# Generated by Django 2.0.9 on 2019-05-08 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0002_auto_20190507_1852'),
    ]

    operations = [
        migrations.AddField(
            model_name='horse',
            name='post_position',
            field=models.IntegerField(null=True),
        ),
    ]
