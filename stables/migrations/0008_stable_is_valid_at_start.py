# Generated by Django 2.0.9 on 2019-05-31 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0007_horse_program_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='stable',
            name='is_valid_at_start',
            field=models.NullBooleanField(),
        ),
    ]