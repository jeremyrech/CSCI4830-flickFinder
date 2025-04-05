from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Additional user information can be added here

# Movie model does most of the heavy lifting here

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    overview = models.TextField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class UserMovieInteraction(models.Model):
    INTERACTION_CHOICES = [
        ('heart', 'Hearted'),
        ('block', 'Blocked'),
        ('watchlist', 'Added to Watchlist'),
        ('skip', 'Skipped'),
        ('unwatch', 'Unwatched')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie', 'interaction_type')
    
    @property
    def is_block_active(self):
        if self.interaction_type == 'block':
            # I don't know if this part works, we'll have to wait 3 days
            return datetime.now() - self.timestamp.replace(tzinfo=None) < timedelta(days=3)
        return False

class UserFilter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    genre_ids = models.JSONField(blank=True, null=True) # Comma-separated genre IDs
    min_release_year = models.IntegerField(null=True, blank=True)
    max_release_year = models.IntegerField(null=True, blank=True)
    min_rating = models.FloatField(null=True, blank=True)
    # Add more filters as needed
