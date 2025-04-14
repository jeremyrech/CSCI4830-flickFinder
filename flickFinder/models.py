from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Extends the default Django User model to store additional profile information.

    Currently only establishes one-to-one link, but will likely be expanded with profile pic, etc.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Additional user information added here

    def __str__(self):
        """Returns the username of the associated user"""
        return self.user.username

class Movie(models.Model):
    """
    Represents a movie, stores key details fetched from TMDB
    """
    tmdb_id = models.IntegerField(unique=True, help_text="TMDB unique identifier")
    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    overview = models.TextField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True, help_text="Should have minimum of 100 votes")
    genres = models.JSONField(null=True, blank=True, help_text="List of genre dicts, e.g., [{'id': 28, 'name': 'Action'}]")
    
    def __str__(self):
        """Returns the title of the movie"""
        return self.title

class UserMovieInteraction(models.Model):
    """
    Records interactions between a User and a Movie.

    Tracks actions 'heart', 'block', 'watchlist', 'skip'
    Ensures that a specific interaction type for a user/movie combination is unique
    """
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
        # Index should allow faster lookups if we still use the interactions for everything
        indexes = [
            models.Index(fields=['user', 'interaction_type', 'timestamp']),
        ]
    
    @property
    def is_block_active(self):
        """
        Checks if a 'block' interaction is still considered active (within 3 days)

        Returns:
            bool: True if interaction is 'block' and timestamp <= 3 days ago
        """
        if self.interaction_type == 'block':
            return timezone.now() < self.timestamp + timezone.timedelta(days=3)
        return False

class UserFilter(models.Model):
    """
    Stores user-specific filtering preferences for movie recommendations
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    genre_ids = models.JSONField(blank=True, null=True, default=list)
    min_release_year = models.IntegerField(null=True, blank=True)
    max_release_year = models.IntegerField(null=True, blank=True)
    min_rating = models.FloatField(null=True, blank=True)
    # Add more filters as needed

    def __str__(self):
        """Returns a string representation of the user's filters."""
        return f"Filters for {self.user.username}"

    def clean(self):
        """
        Provides model-level validation, specifically ensuring min_year <= max_year
        """
        super().clean()
        if self.min_release_year and self.max_release_year and self.min_release_year > self.max_release_year:
            logger.warning(f"Validation Error for User {self.user.id}: Min year ({self.min_release_year}) > Max year ({self.max_release_year}).")
            raise ValidationError('Minimum release year cannot be after maximum release year.')
