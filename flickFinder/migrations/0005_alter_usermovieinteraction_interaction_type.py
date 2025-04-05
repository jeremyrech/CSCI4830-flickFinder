# Generated by Django 5.1.6 on 2025-04-05 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flickFinder', '0004_alter_userfilter_genre_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermovieinteraction',
            name='interaction_type',
            field=models.CharField(choices=[('heart', 'Hearted'), ('block', 'Blocked'), ('watchlist', 'Added to Watchlist'), ('skip', 'Skipped'), ('unwatch', 'Unwatched')], max_length=10),
        ),
    ]
