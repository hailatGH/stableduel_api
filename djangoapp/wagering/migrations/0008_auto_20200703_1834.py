# Generated by Django 2.0.9 on 2020-07-03 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagering', '0007_auto_20200701_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='bet',
            name='bet_submitted',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='bet',
            name='chrims_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bet',
            name='chrims_status_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='contest',
            name='chrims_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contest',
            name='chrims_status_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='payout',
            name='chrims_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payout',
            name='chrims_status_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
