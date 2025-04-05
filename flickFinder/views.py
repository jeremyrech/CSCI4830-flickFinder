from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import SignUpForm, FilterForm
from .models import UserMovieInteraction, UserFilter, Movie
from .services.tmdb_service import TMDBService
from django.utils import timezone

# Initialize TMDB service
tmdb_service = TMDBService()

def home(request):
    """Home page with movie recommendations"""
    # Get user filters if logged in
    user_filters = None
    if request.user.is_authenticated:
        user_filters, _ = UserFilter.objects.get_or_create(user=request.user)
    
    # Get filter form
    filter_form = FilterForm(instance=user_filters) if user_filters else FilterForm()
    
    # Get the first movie for display (if available)
    current_movie = None
    if request.user.is_authenticated:
        current_movie = get_next_unwatched_movie(request.user, user_filters)
    
    if current_movie:
        # Store in our database
        current_movie_obj = tmdb_service.get_or_create_movie(current_movie)
    
    context = {
        'movie': current_movie,
        'filter_form': filter_form,
    }
    
    return render(request, 'flickFinder/index.html', context)

def movie_detail(request, movie_id):
    """Movie detail page"""
    # Get movie details from TMDB
    movie_data = tmdb_service.get_movie_details(movie_id)
    
    # Store in our database
    movie = tmdb_service.get_or_create_movie(movie_data)
    
    # Get user interaction with this movie if logged in
    user_interaction = None
    if request.user.is_authenticated:
        user_interaction = UserMovieInteraction.objects.filter(
            user=request.user,
            movie=movie
        ).first()
    
    context = {
        'movie': movie_data,
        'user_interaction': user_interaction,
    }
    
    return render(request, 'flickFinder/movie_detail.html', context)

@login_required
@require_POST
def movie_interaction(request):
    """Handle user interaction with a movie (heart, block, watchlist, unwatch(list), skip)"""
    movie_id = request.POST.get('movie_id')
    interaction_type = request.POST.get('interaction_type')
    
    # Validate interaction type
    if interaction_type not in dict(UserMovieInteraction.INTERACTION_CHOICES):
        return JsonResponse({'status': 'error', 'message': 'Invalid interaction type'})
    
    # Get movie from TMDB and store in our database
    movie_data = tmdb_service.get_movie_details(movie_id)
    movie = tmdb_service.get_or_create_movie(movie_data)
    
    # Record the interaction
    UserMovieInteraction.objects.update_or_create(
        user=request.user,
        movie=movie,
        interaction_type=interaction_type,
        defaults={'timestamp': timezone.now()}
    )
    
    # Get next movie recommendation
    user_filters, _ = UserFilter.objects.get_or_create(user=request.user)

    next_movie = get_next_unwatched_movie(request.user, user_filters)
    
    if next_movie:
        return JsonResponse({
            'status': 'success',
            'next_movie': next_movie
        })
    else:
        return JsonResponse({
            'status': 'no_more_movies',
            'message': 'No more movies to show with current filters'
        })

def get_next_unwatched_movie(user, filters, current_page=1, max_pages=5):
    """Helper function to find an unwatched movie, paginating if necessary"""
    movies = tmdb_service.discover_movies(filters, page=current_page)
    
    # Filter out blocked movies
    active_blocks = []
    for interaction in UserMovieInteraction.objects.filter(
        user=user, 
        interaction_type='block'
    ):
        if interaction.is_block_active:
            active_blocks.append(interaction.movie.tmdb_id) 

    movies = [m for m in movies if m['id'] not in active_blocks]
    
    # Get watched movies
    watched_movies = UserMovieInteraction.objects.filter(
        user=user,
        interaction_type__in=['skip', 'heart', 'block', 'watchlist']
    ).values_list('movie__tmdb_id', flat=True)
    
    # Find first unwatched movie
    for movie in movies:
        if movie['id'] not in watched_movies:
            return movie
    
    if current_page < max_pages:
        return get_next_unwatched_movie(user, filters, current_page + 1, max_pages)
    
    # No unwatched movies found after checking all pages
    return None

@login_required
@require_POST
def save_filters(request):
    """Save user filters"""
    user_filters, _ = UserFilter.objects.get_or_create(user=request.user)
    
    form = FilterForm(request.POST, instance=user_filters)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors})

def signup(request):
    """User signup view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log in the user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'flickFinder/login.html', {'form': form, 'signup': True})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('home')
    
    return render(request, 'flickFinder/login.html', {'signup': False})

@login_required
def watchlist(request):
    """View user's watchlist"""
    watchlist_items = UserMovieInteraction.objects.filter(
        user=request.user,
        interaction_type='watchlist'
    ).select_related('movie')
    
    context = {
        'watchlist': watchlist_items
    }
    
    return render(request, 'flickFinder/watchlist.html', context)

@login_required
@require_POST
def unwatchlist(request):
    # Handle Unwatchlisting
    movie_id_str = request.POST.get('movie_id')
    movie_id = int(movie_id_str)

    movie = get_object_or_404(Movie, tmdb_id=movie_id) # Ensure movie exists

    # Get the specific movie object
    temp = UserMovieInteraction.objects.get(
        user=request.user,
        movie=movie,
        interaction_type='watchlist'
    )

    # Set interaction type to skip and save
    temp.interaction_type = 'skip'
    temp.save()

    return JsonResponse({'message': 'Removed From Watchlist'}, status=200)