# Generated by Django 2.0.9 on 2020-01-31 23:15

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0019_auto_20191108_1552'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('follows', '0005_auto_20200128_1437'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='follows',
            unique_together={('owner', 'user')},
        ),
    ]
