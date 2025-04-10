from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from .forms import SignUpForm, FilterForm
from .models import UserMovieInteraction, UserFilter, Movie
from .services.tmdb_service import TMDBService, TMDBServiceError
from django.utils import timezone
from django.db.models import Count, Q
import logging
from collections import Counter
import random

logger = logging.getLogger(__name__)
BATCH_FETCH_PAGES = 5
MAX_TMDB_PAGE = 500

# Initialize TMDB service
tmdb_service = TMDBService()

def _get_excluded_ids(user):
    """ Helper for get_next_movie_for_user to get excluded ids for pre-filtering """
    try:
        excluded_interactions = UserMovieInteraction.objects.filter(user=user)
        excluded_tmdb_ids = set(excluded_interactions.values_list('movie__tmdb_id', flat=True))
        three_days_ago = timezone.now() - timezone.timedelta(days=3)
        actively_blocked_ids = set(UserMovieInteraction.objects.filter(
            user=user, interaction_type='block', timestamp__gte=three_days_ago
        ).values_list('movie__tmdb_id', flat=True))
        excluded_tmdb_ids.update(actively_blocked_ids)
        logger.debug(f"User {user.id} excluded IDs count: {len(excluded_tmdb_ids)}")
        return excluded_tmdb_ids
    except Exception as e:
        logger.exception(f"Error retrieving excluded interactions for user {user.id}, {e}")
        return set() # Return empty set on error

def _get_next_movie_for_user(request, tmdb_service, apply_filters=True): # Pass request for session, death death death
    """ Attempts to serve from cache first. If cache is empty, fetches a batch"""
    user = request.user # Get user from request
    session_key = f'recommendation_cache_{user.id}' # Unique session key per user
    logger.debug(f"--- Finding next movie for user {user.id} (Session Cache Method) ---")

    # uhhh I also did stuff to tmdb_service for session stuff, that may break a thing or two

    # cache first
    cached_ids = request.session.get(session_key, [])
    source_of_cache = request.session.get(f'{session_key}_source', 'unknown')
    logger.debug(f"User {user.id}: Found {len(cached_ids)} movie IDs in session cache. (Source: {source_of_cache}).")

    while cached_ids:
        movie_id = cached_ids.pop(0) # Get the next ID from the front
        logger.debug(f"Trying cached ID: {movie_id}")

        # Fetch details for cached ID
        try:
            movie_data = tmdb_service.get_movie_details(movie_id)
            if movie_data:
                # Ensure it's saved locally (gets genres etc.)
                movie_obj = tmdb_service.get_or_create_movie(movie_data)
                if movie_obj:
                    logger.info(f"Serving movie '{movie_obj.title}' (ID: {movie_id}) from cache.")
                    request.session[session_key] = cached_ids # Update cache in session
                    request.session.modified = True
                    return movie_data
                else:
                     logger.warning(f"Failed to get/create movie object for cached ID {movie_id}. Skipping.")
                     # Don't add back to cache if it failed get/create
            else:
                # Movie ID might be invalid on TMDB now?
                logger.warning(f"TMDB details fetch returned None for cached ID {movie_id}. Skipping.")
                # Don't add back to cache
        except TMDBServiceError as e:
            logger.error(f"TMDB Service Error fetching details for cached ID {movie_id}: {e}. Skipping.")
        except Exception as e:
            logger.exception(f"Unexpected error processing cached ID {movie_id}. Skipping.")

        # Update cache in session if loop continues
        request.session[session_key] = cached_ids
        request.session.modified = True

    # Cache is empty or exhausted - Fetch a new batch
    logger.info(f"Session cache empty or exhausted for user {user.id}. Fetching new batch...")
    excluded_tmdb_ids = _get_excluded_ids(user) # Get current list of blocked

    # get filters for new batch
    user_filters = None
    fetch_with_filters = False
    if apply_filters:
        try:
            user_filters, _ = UserFilter.objects.get_or_create(user=user) # can use user since we already do the request thing earlier
            if user_filters and (user_filters.genre_ids or user_filters.min_release_year or
                                 user_filters.max_release_year or user_filters.min_rating):
                fetch_with_filters = True
                logger.debug(f"Using filters for batch fetch: {user_filters.__dict__ if user_filters else 'None'}")
            else:
                logger.info(f"apply_filters=true, but no filters set by user {user.id}. Fetching without filters.")
        except Exception as e:
             logger.exception(f"Error retrieving UserFilter for user {user.id}. Fetching without filters.")
             fetch_with_filters = False

    # fetch batch
    potential_movies = {} # Use dict to automatically handle duplicates by ID
    cache_source_name = "unknown" # starts unknown to debug if unknown is passed

    if fetch_with_filters:
        cache_source_name = "filtered"
        logger.info(f"Starting filtered batch fetch for user {user.id}...")
        # Initial call to get total_pages for this filter set, may be unoptimized
        try:
            _, initial_total_pages = tmdb_service.discover_movies(user_filters, page=1)
            logger.info(f"Filter query initial total_pages = {initial_total_pages}")
        except Exception as e:
            logger.exception("Error during initial filtered call to get total_pages.")
            initial_total_pages = 0 # Assume failure means no results

        if initial_total_pages == 0:
            logger.warning(f"No results found for user {user.id}'s filters (total_pages=0). No movies to cache or serve.")
            request.session[session_key] = [] # Ensure cache is empty
            request.session[f'{session_key}_source'] = cache_source_name
            request.session.modified = True
            return None

        # Determine pages to sample within the available range
        search_max_page = min(initial_total_pages, MAX_TMDB_PAGE)
        # May likely need to adjust this to search_max_page - 1, as last page is likely incomplete
        # Trying to iterate over last page may lead to errors, but it could also be fine, so I'm leaving it
        num_pages_to_sample = min(BATCH_FETCH_PAGES, search_max_page)
        if num_pages_to_sample > 0: # This should never happen, as we already checked for 0 results
             # Sample randomly within the available pages for these filters
             pages_to_fetch = random.sample(range(1, search_max_page + 1), num_pages_to_sample)
             logger.debug(f"Fetching filtered batch from pages: {pages_to_fetch} (out of {search_max_page} available)")

             for page_num in pages_to_fetch:
                 try:
                     movies_page, _ = tmdb_service.discover_movies(user_filters, page=page_num)
                     if movies_page:
                         logger.debug(f"Fetched {len(movies_page)} movies from filtered page {page_num}")
                         for movie_data in movies_page:
                             if movie_data and movie_data.get('id'): potential_movies[movie_data['id']] = movie_data
                 except Exception as e: logger.exception(f"Error fetching filtered page {page_num}")
        else:
            logger.warning(f"Cannot sample pages for filtered results (num_pages_to_sample=0).")
    # Simple popular fetch
    else: # fetch_with_filters is False
        cache_source_name = "popular"
        logger.info(f"Starting popular batch fetch for user {user.id}...")
        # Likely will want to change this to a range of 1-500, but I'm leaving it for now
        pages_to_fetch = random.sample(range(1, MAX_TMDB_PAGE + 1), BATCH_FETCH_PAGES)
        logger.debug(f"Fetching popular batch from pages: {list(pages_to_fetch)}")
        for page_num in pages_to_fetch:
            try:
                movies_page, _ = tmdb_service.get_popular_movies(page=page_num)
                if movies_page:
                    logger.debug(f"Fetched {len(movies_page)} movies from popular page {page_num}")
                    for movie_data in movies_page:
                        if movie_data and movie_data.get('id'): potential_movies[movie_data['id']] = movie_data
            except Exception as e: logger.exception(f"Error fetching popular page {page_num}")
    # start filtering and cache
    logger.info(f"Batch fetch complete. Total unique potential movies fetched: {len(potential_movies)}")
    valid_movie_ids = [tmdb_id for tmdb_id in potential_movies if tmdb_id not in excluded_tmdb_ids]
    logger.info(f"Found {len(valid_movie_ids)} valid (non-excluded) movies in the batch.")

    if valid_movie_ids:
        random.shuffle(valid_movie_ids)
        request.session[session_key] = valid_movie_ids
        request.session[f'{session_key}_source'] = cache_source_name # Store source type
        request.session.modified = True
        logger.debug(f"Cached {len(valid_movie_ids)} shuffled IDs (Source: {cache_source_name}).")

        # Serve first item from new cache
        newly_cached_id = valid_movie_ids.pop(0) # Get first ID
        logger.debug(f"Attempting to serve first item from new cache: {newly_cached_id}")
        try:
            movie_data = tmdb_service.get_movie_details(newly_cached_id)
            if movie_data:
                movie_obj = tmdb_service.get_or_create_movie(movie_data)
                if movie_obj:
                     logger.info(f"Serving movie '{movie_obj.title}' (ID: {newly_cached_id}) immediately after batch fetch.")
                     request.session[session_key] = valid_movie_ids # Update remaining cache
                     request.session.modified = True
                     return movie_data
                else: logger.warning(f"Failed get/create for newly cached ID {newly_cached_id}.")
            else: logger.warning(f"TMDB details None for newly cached ID {newly_cached_id}.")
        except Exception as e: logger.exception(f"Unexpected error processing newly cached ID {newly_cached_id}")
        # If serving first item failed, update session cache anyway before returning None
        request.session[session_key] = valid_movie_ids
        request.session.modified = True

    # Batch fetch yielded no valid movies OR serving first failed
    logger.warning(f"Failed to find or serve a suitable movie after batch fetch (Source: {cache_source_name}) for user {user.id}.")
    request.session[session_key] = [] # Ensure cache is empty
    request.session[f'{session_key}_source'] = cache_source_name
    request.session.modified = True
    return None # No movie found

    # reminder: I may want to add a popular fetch as a backup or prompt user with popular button, but that's js in index

def home(request):
    """Home page with movie recommendations"""
    current_movie_data = None
    filter_form = FilterForm() # Initialize form

    if request.user.is_authenticated:
        user_filters, _ = UserFilter.objects.get_or_create(user=request.user)
        filter_form = FilterForm(instance=user_filters) # Populate form with user's filters

        # Uses helper function for next movie
        current_movie_data = _get_next_movie_for_user(request, tmdb_service)

    context = {
        'movie': current_movie_data, # Pass movie dict
        'filter_form': filter_form,
    }
    
    context = {
        'movie': current_movie_data,
        'filter_form': filter_form,
    }
    
    return render(request, 'flickFinder/index.html', context)

def movie_detail(request, movie_id):
    """Movie detail page"""
    # Get movie details from TMDB
    try:
        movie_data = tmdb_service.get_movie_details(movie_id)
        if not movie_data:
             raise Http404("Movie details could not be retrieved from TMDB.")
        # Ensure movie exists in our DB
        movie = tmdb_service.get_or_create_movie(movie_data)
        if not movie: # Handle case where movie couldn't be created/retrieved
            raise Http404("Movie could not be found or created in the database.")
    except TMDBServiceError:
         raise Http404("Error communicating with the movie database.")
    except ValueError: # Catch potential errors if movie_id is invalid format
         raise Http404("Invalid movie ID format.")
    
    # Get user interaction with this movie if logged in
    user_interaction = None
    if request.user.is_authenticated:
        user_interaction = UserMovieInteraction.objects.filter(
            user=request.user, movie=movie
        ).order_by('-timestamp').first() # most recent
    
    context = {
        'movie_data': movie_data,
        'movie_obj': movie,
        'user_interaction': user_interaction,
    }
    
    return render(request, 'flickFinder/movie_detail.html', context)

@login_required
@require_POST
def movie_interaction(request):
    """Handle user interaction with a movie (heart, block, watchlist, skip)"""
    movie_id_str = request.POST.get('movie_id')
    interaction_type = request.POST.get('interaction_type')
    
    # Validate interaction type
    if not movie_id_str or not movie_id_str.isdigit():
        return JsonResponse({'status': 'error', 'message': 'Invalid Movie ID.'}, status=400)
    movie_id = int(movie_id_str)

    if interaction_type not in dict(UserMovieInteraction.INTERACTION_CHOICES):
        return JsonResponse({'status': 'error', 'message': 'Invalid interaction type'}, status=400)
    
    # Get movie from TMDB and store in db
    movie = Movie.objects.filter(tmdb_id=movie_id).first()
    if not movie:
        try:
            movie_data = tmdb_service.get_movie_details(movie_id)
            if not movie_data:
                 return JsonResponse({'status': 'error', 'message': 'Could not retrieve movie details.'}, status=503) # Service unavailable?
            movie = tmdb_service.get_or_create_movie(movie_data)
            if not movie:
                 return JsonResponse({'status': 'error', 'message': 'Could not save movie locally.'}, status=500)
        except TMDBServiceError:
             return JsonResponse({'status': 'error', 'message': 'Error communicating with movie service.'}, status=503)
    
    # Record the interaction
    interaction, created = UserMovieInteraction.objects.update_or_create(
            user=request.user,
            movie=movie,
            interaction_type=interaction_type,
            defaults={'timestamp': timezone.now()}
    )
    logger.info(f"Recorded interaction: User {request.user.id}, Movie {movie_id}, Type {interaction_type}, Created: {created}")

    
    # Get next movie recommendation using the helper
    next_movie_data = _get_next_movie_for_user(request, tmdb_service)

    if next_movie_data:
        return JsonResponse({
            'status': 'success',
            'next_movie': next_movie_data # Send movie data dictionary
        })
    else:
        return JsonResponse({
            'status': 'no_more_movies',
            'message': 'No more movies match your criteria. Try adjusting filters!'
        })

@login_required
@require_POST
def save_filters(request):
    """Save user filters"""
    user_filters, _ = UserFilter.objects.get_or_create(user=request.user)
    
    form = FilterForm(request.POST, instance=user_filters)
    if form.is_valid():
        form.save()
        session_key = f'recommendation_cache_{request.user.id}'
        if session_key in request.session:
            del request.session[session_key]
            logger.info(f"Cleared recommendation cache for user {request.user.id} due to filter change.")
        logger.info(f"Saved filters for user {request.user.id}: {form.cleaned_data}")
        new_first_movie = _get_next_movie_for_user(request, tmdb_service)
        return JsonResponse({
            'status': 'success',
            'next_movie': new_first_movie # Send next movie based on new filters
        })
    else:
        logger.warning(f"Filter form invalid for user {request.user.id}: {form.errors.as_json()}")
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

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
            logger.info(f"New user signed up and logged in: {user.username}")
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'flickFinder/login.html', {'form': form, 'signup': True})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"User logged in: {username}")
            next_url = request.POST.get('next', request.GET.get('next', ''))
            return redirect(next_url or 'home')
        else:
            logger.warning(f"Login failed for username: {username}")
            pass
    return render(request, 'flickFinder/login.html', {'signup': False})

@login_required
def watchlist(request):
    """View user's watchlist"""
    watchlist_items = UserMovieInteraction.objects.filter(
        user=request.user,
        interaction_type='watchlist'
    ).select_related('movie').order_by('-timestamp')
    
    # Get user interaction statistics
    stats_queryset = UserMovieInteraction.objects.filter(user=request.user)
    user_stats = stats_queryset.aggregate(
        watchlist_count=Count('id', filter=Q(interaction_type='watchlist')),
        heart_count=Count('id', filter=Q(interaction_type='heart')),
        skip_count=Count('id', filter=Q(interaction_type='skip')),
        block_count=Count('id', filter=Q(interaction_type='block')),
        total_interactions=Count('id')
    )
    user_stats['join_date'] = request.user.date_joined
    user_stats['last_login'] = request.user.last_login

    
    # Get genre preferences based on hearted and watchlisted movies
    genre_preferences = []
    try:
        positive_interaction_movie_ids = UserMovieInteraction.objects.filter(
            user=request.user,
            interaction_type__in=['heart', 'watchlist']
        ).values_list('movie_id', flat=True).distinct() # Get unique movies
    
        movies_with_genres = Movie.objects.filter(
            id__in=positive_interaction_movie_ids,
            genres__isnull=False # Only consider movies where genres are saved
        )

        genre_counter = Counter()
        for movie in movies_with_genres:
            # Assumes movie.genres stores a list like [{'id': 28, 'name': 'Action'}, ...]
            if isinstance(movie.genres, list):
                 for genre in movie.genres:
                     if isinstance(genre, dict) and 'name' in genre:
                         genre_counter[genre['name']] += 1
        # Get 5 most common genres, list of tuples
        top_genres = genre_counter.most_common(5)

        # Format for template (list of dictionaries)
        genre_preferences = [{'name': name, 'count': count} for name, count in top_genres]
        logger.debug(f"Calculated genre preferences for user {request.user.id}: {genre_preferences}")
    except Exception as e:
        logger.error(f"Error calculating genre preferences for user {request.user.id}: {e}", exc_info=True)

    # Get filters
    user_filters, _ = UserFilter.objects.get_or_create(user=request.user)
    # Pass the form for potential display/editing on watchlist page?
    filter_form = FilterForm(instance=user_filters)

    context = {
        'watchlist': watchlist_items,
        'user_stats': user_stats,
        'genre_preferences': genre_preferences,
        'user_filters': user_filters,
        'filter_form': filter_form,
    }
    
    return render(request, 'flickFinder/watchlist.html', context)

@login_required
@require_POST
def unwatchlist(request):
    movie_id_str = request.POST.get('movie_id')
    if not movie_id_str or not movie_id_str.isdigit():
        return JsonResponse({'status': 'error', 'message': 'Invalid Movie ID.'}, status=400)
    movie_id = int(movie_id_str)

    movie = get_object_or_404(Movie, tmdb_id=movie_id) # Ensure movie exists

    temp = UserMovieInteraction.objects.get(
        user=request.user,
        movie=movie,
        interaction_type='watchlist'
    )

    # Set interaction type to skip and save
    temp.interaction_type = 'skip'
    temp.save()

    if temp:
        logger.info(f"Removed movie {movie_id} from watchlist for user {request.user.id}")
        return JsonResponse({'status': 'success', 'message': 'Removed from watchlist'})
    else:
        logger.warning(f"Attempted to remove movie {movie_id} from watchlist for user {request.user.id}, but it wasn't found.")
        # It's okay if it wasn't found, still return success for UI consistency
        return JsonResponse({'status': 'success', 'message': 'Movie not found on watchlist, considered removed.'})