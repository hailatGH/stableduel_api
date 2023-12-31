# Generated by Django 2.0.9 on 2019-05-07 18:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('racecards', '0002_racecard_races'),
        ('stables', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stable',
            old_name='horses',
            new_name='runners',
        ),
        migrations.AddField(
            model_name='horse',
            name='external_id',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='horse',
            name='jockey',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='horse',
            name='owner',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='horse',
            name='race_number',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='horse',
            name='racecard',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='racecards.Racecard'),
        ),
        migrations.AddField(
            model_name='horse',
            name='scratched',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='horse',
            name='trainer',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
