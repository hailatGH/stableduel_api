# Generated by Django 2.0.9 on 2019-05-29 13:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=140)),
                ('message', models.CharField(max_length=280)),
                ('notif_type', models.CharField(blank=True, choices=[('scratch', 'Scratch'), ('stable_incomplete', 'Stable Incomplete'), ('first_post', 'Fist Post'), ('race_scores_posted', 'Race Scores Posted'), ('race_canceled', 'Race Canceled'), ('race_completed', 'Race Completed'), ('race_results_posted', 'Race Results Posted'), ('game_canceled', 'Game Canceled')], default=None, max_length=25, null=True)),
                ('action', models.CharField(blank=True, choices=[('go_to_stable', 'Go to Stable'), ('go_to_leaderboard', 'Go to Leaderboard'), ('none', 'None')], default=None, max_length=25, null=True)),
                ('is_dismissible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
