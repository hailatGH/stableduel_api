# Generated by Django 2.0.9 on 2020-06-19 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagering', '0003_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='abbreviation',
            field=models.CharField(default='', max_length=2),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='state',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
