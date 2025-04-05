from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('interaction/', views.movie_interaction, name='movie_interaction'),
    path('watchlist/delete/', views.unwatchlist, name='unwatchlist'),
    path('filters/', views.save_filters, name='save_filters'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('watchlist/', views.watchlist, name='watchlist'),
]