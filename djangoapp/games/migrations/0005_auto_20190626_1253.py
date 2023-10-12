# Generated by Django 2.0.9 on 2019-06-26 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_game_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='game',
            name='game_state',
            field=models.CharField(choices=[('OPEN', 'Open'), ('LIVE', 'Live'), ('RESULTS_PENDING', 'Results Pending'), ('FINISHED', 'Finished'), ('CANCELLED', 'Cancelled')], default='OPEN', max_length=20),
        ),
        migrations.AddField(
            model_name='game',
            name='published',
            field=models.BooleanField(default=True),
        ),
    ]
