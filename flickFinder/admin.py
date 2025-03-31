from django.contrib import admin
from .models import UserProfile, Movie, UserMovieInteraction, UserFilter

admin.site.register(UserProfile)
admin.site.register(Movie)
admin.site.register(UserMovieInteraction)
admin.site.register(UserFilter)
# Register your models here.