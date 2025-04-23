from django.urls import path
from . import views

urlpatterns = [
    # Home discover page
    path('', views.home, name='home'),

    # Movie detail page, uses movie_id to fetch detailed movie info
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),

    # API endpoint, handles user interactions via POST requests
    path('interaction/', views.movie_interaction, name='movie_interaction'),

    # API endpoint, handles removing a movie from the watchlist via POST request
    path('watchlist/delete/', views.unwatchlist, name='unwatchlist'),

    # API endpoint, handles saving user filters via POST request
    path('filters/', views.save_filters, name='save_filters'),

    # Authentication, login page/handler
    path('login/', views.user_login, name='login'),

    # Authentication, signup page/handler
    path('signup/', views.signup, name='signup'),

    # Watchlist page, displays user's watchlist
    path('watchlist/', views.watchlist, name='watchlist'),

    # logout included in django auth

    path('search/', views.search_movies, name='search_movies'),
]
