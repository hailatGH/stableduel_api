# Generated by Django 2.0.9 on 2020-04-14 12:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horse_points', '0002_auto_20200414_0143'),
        ('follows', '0009_remove_follows_horse_point'),
    ]

    operations = [
        migrations.AddField(
            model_name='follows',
            name='horse_point',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='horse_points.HorsePoint'),
        ),
    ]
