from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q
import logging
import random
from collections import Counter

from .forms import SignUpForm, FilterForm
from .models import UserMovieInteraction, UserFilter, Movie
from .services.tmdb_service import TMDBService, TMDBServiceError

logger = logging.getLogger(__name__)
BATCH_FETCH_PAGES = 5
MAX_TMDB_PAGE = 500

# Initialize TMDB service
tmdb_service = TMDBService()

def _get_excluded_ids(user):
    """
    Retrieves a set of TMDB movie IDs that should be excluded for a given user.

    Excludes movies the user has interacted with first, then separately
    the movies actively blocked (within the last 3 days).

    Args:
        user (User): The user to retrieve excluded IDs for. From request.user

    Returns:
        set: A set of TMDB movie IDs to exclude. Returns an empty set on error.
    """
    try:
        excluded_interactions = UserMovieInteraction.objects.filter(user=user).exclude(interaction_type='block')
        excluded_tmdb_ids = set(excluded_interactions.values_list('movie__tmdb_id', flat=True))
        three_days_ago = timezone.now() - timezone.timedelta(days=3)
        actively_blocked_ids = set(UserMovieInteraction.objects.filter(
            user=user,
            interaction_type='block',
            timestamp__gte=three_days_ago
        ).values_list('movie__tmdb_id', flat=True))
        logger.debug(f"User {user.id} actively blocked IDs: {len(actively_blocked_ids)}")
        excluded_tmdb_ids.update(actively_blocked_ids)
        logger.debug(f"User {user.id} total excluded IDs count: {len(excluded_tmdb_ids)}")
        return excluded_tmdb_ids
    except Exception as e:
        logger.exception(f"Error retrieving excluded interactions for user {user.id}, {e}")
        return set() # Return empty set on error

def _get_next_movie_for_user(request, tmdb_service, apply_filters=True): # Pass request for session, death death death
    """
    Gets the next movie recommendation for the logged-in* user.

    Attempts to serve from a per-user session cache first. If the cache is
    empty or exhausted, fetches a new batch of potential movies from TMDB
    from filters primarily, but goes to popular if none available, filters out excluded movies,
    caches the results, and returns the first movie from the new batch.

    Args:
        request (HttpRequest): The incoming HTTP request object (used for user and session).
        tmdb_service (TMDBService): An instance of the TMDB service.

    Returns:
        dict: A dictionary containing TMDB movie data for the next recommendation,
              or None if no suitable movie could be found or an error occurred.
    """
    user = request.user # Get user from request
    session_key = f'recommendation_cache_{user.id}' # Unique session key per user
    logger.debug(f"--- Finding next movie for user {user.id} (Session Cache Method) ---")

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
                # Ensure it's saved locally (important for watchlist, gets genres etc.)
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
        except Exception as e: 
            logger.exception(f"Unexpected error processing newly cached ID {newly_cached_id}")
            request.session[session_key] = valid_movie_ids
            request.session.modified = True
            return None # expanded to indicate failure on full exception

    # Batch fetch yielded no valid movies OR serving first failed
    logger.warning(f"Failed to find or serve a suitable movie after batch fetch (Source: {cache_source_name}) for user {user.id}.")
    request.session[session_key] = [] # Ensure cache is empty
    request.session[f'{session_key}_source'] = cache_source_name
    request.session.modified = True
    return None # No movie found

    # reminder: I may want to add a popular fetch as a backup or prompt user with popular button, but that's js in index

def home(request):
    """
    Renders the home page (index.html).

    For authenticated users, it attempts to get next movie recommendation
    using `_get_next_movie_for_user` and prepares filter form.
    For anonymous users, it shows a welcome/login prompt.

    Future todo: add non-login functionality

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered home page.
    """
    logger.debug(f"Home page request received. User authenticated: {request.user.is_authenticated}")
    current_movie_data = None
    filter_form = None # Delay initialization of form

    if request.user.is_authenticated:
        logger.debug(f"User '{request.user.username}' is authenticated. Getting filters and next movie.")
        try:
            user_filters, created = UserFilter.objects.get_or_create(user=request.user)
            if created:
                logger.info(f"Created UserFilter object for user {request.user.id}")
            filter_form = FilterForm(instance=user_filters) # Populate form with user's filters
        except Exception as e:
            logger.exception(f"Error getting/creating UserFilter for user {request.user.id}. Filter form will be empty.")
            filter_form = FilterForm() # Provide an empty form on error

        # Uses helper function for next movie recommendation
        current_movie_data = _get_next_movie_for_user(request, tmdb_service)
    else:
        filter_form = FilterForm() # Empty form for anonymous users as well

    context = {
        'movie': current_movie_data, # Pass movie dict
        'filter_form': filter_form,
    }
    logger.debug(f"Rendering home page with context: movie_present={bool(current_movie_data)}, filter_form_present={bool(filter_form)}")
    return render(request, 'flickFinder/index.html', context)

def movie_detail(request, movie_id):
    """
    Renders the movie detail page (movie_detail.html).

    Fetches detailed movie information from TMDB using the provided `movie_id`.
    Ensures the movie exists in the local database (creating/updating if necessary).
    Retrieves the latest user interaction with this movie if the user is logged in.

    Args:
        request (HttpRequest): The incoming HTTP request.
        movie_id (int): The TMDB ID of the movie to display.

    Returns:
        HttpResponse: Rendered movie detail page.

    Raises:
        Http404: If the movie_id is invalid, movie details cannot be fetched from TMDB,
                 or the movie cannot be saved/retrieved locally.
    """
    logger.debug(f"Request received for movie detail page. TMDB ID: {movie_id}")

    if not isinstance(movie_id, int) or movie_id <= 0:
        logger.warning(f"Invalid movie ID format received: {movie_id}")
        raise Http404("Invalid movie ID provided.")
    
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
         logger.error(f"TMDB Service Error while fetching details for movie {movie_id}: {e}")
         raise Http404("Error communicating with the movie database.")
    except ValueError: # Catch potential errors if movie_id is invalid format
         logger.warning(f"ValueError encountered processing movie ID: {movie_id}")
         raise Http404("Invalid movie ID format.")
    except Exception as e:
        logger.exception(f"Unexpected error retrieving movie details or object for TMDB ID {movie_id}: {e}")
        raise Http404("An unexpected error occurred retrieving movie information.")
    
    # Get user interaction with this movie if logged in
    user_interaction = None
    if request.user.is_authenticated:
        try:
            user_interaction = UserMovieInteraction.objects.filter(
                user=request.user, movie=movie
            ).order_by('-timestamp').first() # most recent
            if not user_interaction:
                logger.debug(f"No previous interaction found for user {request.user.id} and movie {movie_id}.")
        except Exception as e:
            logger.exception(f"Error retrieving interaction for user {request.user.id} and movie {movie_id}: {e}")

    context = {
        'movie_data': movie_data, # Raw data from TMDB
        'movie_obj': movie, # Local movie model instance
        'user_interaction': user_interaction, # Latest interaction object or None
    }
    return render(request, 'flickFinder/movie_detail.html', context)

@login_required
@require_POST
def movie_interaction(request):
    """
    Handles AJAX POST requests for user interactions with movies (heart, block, etc.).

    Validates input, retrieves/creates the movie locally, records the interaction,
    and returns the next movie recommendation in the JSON response.

    Args:
        request (HttpRequest): The incoming AJAX POST request.
            Expects 'movie_id' and 'interaction_type' in POST data.

    Returns:
        JsonResponse: Contains status ('success', 'error', 'no_more_movies')
                      and occasionally 'next_movie' data or an error 'message'.
    """
    movie_id_str = request.POST.get('movie_id')
    interaction_type = request.POST.get('interaction_type')
    
    # Validate interaction type
    if not movie_id_str or not movie_id_str.isdigit():
        logger.warning(f"Invalid Movie ID received in interaction request: '{movie_id_str}' from User {request.user.id}")
        return JsonResponse({'status': 'error', 'message': 'Invalid Movie ID.'}, status=400)
    movie_id = int(movie_id_str)

    if interaction_type not in dict(UserMovieInteraction.INTERACTION_CHOICES):
        logger.warning(f"Invalid interaction type received: '{interaction_type}' from User {request.user.id}")
        return JsonResponse({'status': 'error', 'message': 'Invalid interaction type'}, status=400)
    
    # Get movie from TMDB and store in db
    movie = Movie.objects.filter(tmdb_id=movie_id).first()
    if not movie:
        logger.info(f"Movie with TMDB ID {movie_id} not found locally. Fetching details from TMDB.")
        try:
            movie_data = tmdb_service.get_movie_details(movie_id)
            if not movie_data:
                logger.error(f"Could not retrieve movie details from TMDB for ID {movie_id} during interaction.")
                return JsonResponse({'status': 'error', 'message': 'Could not retrieve movie details.'}, status=503) # Service unavailable?
            movie = tmdb_service.get_or_create_movie(movie_data)
            if not movie:
                return JsonResponse({'status': 'error', 'message': 'Could not save movie locally.'}, status=500)
        except TMDBServiceError as e:
            logger.error(f"TMDB Service Error during interaction for movie {movie_id}: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error communicating with movie service.'}, status=503)
        except Exception as e:
            logger.exception(f"Unexpected error getting/creating movie {movie_id} during interaction: {e}")
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred processing the movie.'}, status=500)
    
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
        logger.info(f"No more suitable movies found for User {request.user.id} after interaction.")
        return JsonResponse({
            'status': 'no_more_movies',
            'message': 'No more movies match your criteria. Try adjusting filters!'
        })

@login_required
@require_POST
def save_filters(request):
    """
    Handles AJAX POST requests to save or update user's movie filters.

    Validates the submitted filter form data. If valid, saves the filters,
    clears the user's recommendation cache, and returns the first movie
    matching the new filters.

    Args:
        request (HttpRequest): The incoming AJAX POST request containing filter form data.

    Returns:
        JsonResponse: Contains status ('success', 'error') and occasionally
                      'next_movie' data or form 'errors'.
    """
    logger.debug(f"Save filters request received for User {request.user.id}.")


    try:
        user_filters, created = UserFilter.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new UserFilter object for User {request.user.id} during save.")

        # Initialize the form with POST data and the user's filter instance
        form = FilterForm(request.POST, instance=user_filters)

        if form.is_valid():
            logger.debug(f"Filter form is valid for User {request.user.id}. Saving filters...")
            form.save()
            session_key = f'recommendation_cache_{request.user.id}'
            if session_key in request.session:
                try:
                    del request.session[session_key]
                    # Also remove the source key
                    cache_source_key = f'{session_key}_source'
                    if cache_source_key in request.session:
                         del request.session[cache_source_key]
                    request.session.modified = True
                    logger.info(f"Cleared recommendation cache for user {request.user.id} due to filter change.")
                except KeyError:
                     logger.warning(f"Tried to delete session key '{session_key}' but wasn't found for user {request.user.id}.")
                except Exception as e:
                    logger.exception(f"Error clearing session cache for user {request.user.id}: {e}")

            logger.info(f"Saved filters for user {request.user.id}: {form.cleaned_data}")
            new_first_movie = _get_next_movie_for_user(request, tmdb_service)
            if new_first_movie:
                 logger.debug(f"Returning new first movie '{new_first_movie.get('title')}' after filter save for user {request.user.id}")
                 return JsonResponse({
                     'status': 'success',
                     'next_movie': new_first_movie # Send movie data dictionary
                 })
            else:
                 logger.info(f"No movies found matching the new filters for user {request.user.id}.")
                 return JsonResponse({
                     'status': 'success', # Saving filters was successful, even if no movies match
                     'next_movie': None, # Indicate no movie found
                     'message': 'Filters saved, but no movies match your new criteria.'
                 })
        else:
            logger.warning(f"Filter form invalid for user {request.user.id}: {form.errors.as_json()}")
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error saving filters for user {request.user.id}: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred while saving filters.'}, status=500)

def signup(request):
    """
    Handles user registration (signup).

    Displays the signup form on GET request.
    Processes the form on POST, creates the user if valid, logs them in,
    and redirects to the home page.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered signup/login page or redirect to home.
    """
    if request.method == 'POST':
        logger.debug("Signup POST request received.")
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Log in the user
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                logger.info(f"New user signed up and logged in: {user.username}")
                return redirect('home')
            except Exception as e:
                 logger.exception(f"Error during user creation or login after signup: {e}")
                 pass # pass through for now, need to work on this
        else:
            # Form is invalid, log errors and re-render the page
            logger.warning(f"Signup form invalid. Errors: {form.errors.as_json()}")
    else:
        form = SignUpForm()

    return render(request, 'flickFinder/login.html', {'form': form, 'signup': True})

def user_login(request):
    """
    Handles user login.

    Displays the login form on GET request.
    Processes login credentials on POST, authenticates the user, logs them in,
    and redirects to the intended destination or home page.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered login page or redirect.
    """
    if request.method == 'POST':
        logger.debug("Login POST request received.")
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            logger.warning("Login attempt with missing username or password.")
            # need to add error message to be displayed directly on login render
            return render(request, 'flickFinder/login.html', {'error': 'Please provide both username and password.', 'signup': False})

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                login(request, user)
                logger.info(f"User logged in: {username}")
                next_url = request.POST.get('next', request.GET.get('next', ''))
                return redirect(next_url or 'home')
            except Exception as e:
                logger.exception(f"Error during login process for user '{username}': {e}")
                return render(request, 'flickFinder/login.html', {'error': 'Invalid username or password.', 'signup': False})
        else:
            logger.warning(f"Login failed for username: {username}")
            return render(request, 'flickFinder/login.html', {'error': 'Invalid username or password.', 'signup': False})
    else:
        # else for GET request to display login form
        logger.debug("Login GET request received, displaying form.")
        next_url = request.GET.get('next', '') # for redirection after login form
        context = {'signup': False, 'next': next_url}
        return render(request, 'flickFinder/login.html', context) # edited to follow similar format

@login_required
def watchlist(request):
    """
    Renders the user's watchlist page (watchlist.html).

    Retrieves movies the user has added to their watchlist.
    Calculates user statistics (interaction counts).
    Calculates basic genre preferences based on hearted/watchlisted movies.
    Retrieves user's saved filters.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered watchlist page.
    """
    logger.debug(f"Watchlist page request received for User {request.user.id}")

    watchlist_items = UserMovieInteraction.objects.filter(
        user=request.user,
        interaction_type='watchlist'
    ).select_related('movie').order_by('-timestamp')

    
    # Get user interaction statistics
    user_stats = {} # initialize empty dict
    stats_queryset = UserMovieInteraction.objects.filter(user=request.user)
    try:
        user_stats = stats_queryset.aggregate(
            watchlist_count=Count('id', filter=Q(interaction_type='watchlist')),
            heart_count=Count('id', filter=Q(interaction_type='heart')),
            skip_count=Count('id', filter=Q(interaction_type='skip')),
            block_count=Count('id', filter=Q(interaction_type='block')),
            total_interactions=Count('id')
        )
        user_stats['join_date'] = request.user.date_joined
        user_stats['last_login'] = request.user.last_login
        logger.debug(f"Calculated user stats for User {request.user.id}: {user_stats}")
    except Exception as e:
        logger.exception(f"Error calculating statistics for User {request.user.id}: {e}")

    
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
        ).exclude(genres__exact=[])

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
        logger.info(f"Calculated genre preferences for user {request.user.id}: {genre_preferences}")
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
        'user_filters': user_filters, # model instance
        'filter_form': filter_form, # form instance for rendering
        
    }
    return render(request, 'flickFinder/watchlist.html', context)

@login_required
def likelist(request):
    """
    Renders the user's watchlist page (watchlist.html).

    Retrieves movies the user has added to their watchlist.
    Calculates user statistics (interaction counts).
    Calculates basic genre preferences based on hearted/watchlisted movies.
    Retrieves user's saved filters.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered watchlist page.
    """
    logger.debug(f"Watchlist page request received for User {request.user.id}")

    watchlist_items = UserMovieInteraction.objects.filter(
        user=request.user,
        interaction_type='watchlist'
    ).select_related('movie').order_by('-timestamp')

    likelist_items = UserMovieInteraction.objects.filter(
        user=request.user,
        interaction_type='heart'
    ).select_related('movie').order_by('-timestamp')
    
    # Get user interaction statistics
    user_stats = {} # initialize empty dict
    stats_queryset = UserMovieInteraction.objects.filter(user=request.user)
    try:
        user_stats = stats_queryset.aggregate(
            watchlist_count=Count('id', filter=Q(interaction_type='watchlist')),
            heart_count=Count('id', filter=Q(interaction_type='heart')),
            skip_count=Count('id', filter=Q(interaction_type='skip')),
            block_count=Count('id', filter=Q(interaction_type='block')),
            total_interactions=Count('id')
        )
        user_stats['join_date'] = request.user.date_joined
        user_stats['last_login'] = request.user.last_login
        logger.debug(f"Calculated user stats for User {request.user.id}: {user_stats}")
    except Exception as e:
        logger.exception(f"Error calculating statistics for User {request.user.id}: {e}")

    
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
        ).exclude(genres__exact=[])

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
        logger.info(f"Calculated genre preferences for user {request.user.id}: {genre_preferences}")
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
        'user_filters': user_filters, # model instance
        'filter_form': filter_form, # form instance for rendering
        'likelist' : likelist_items,
    }
    return render(request, 'flickFinder/likelist.html', context)


@login_required
@require_POST
def unwatchlist(request):
    """
    Handles AJAX POST request to remove a movie from the user's watchlist.

    Instead of deleting the interaction, it changes the interaction_type
    from 'watchlist' to 'skip' to maintain interaction history but effectively
    remove it from the displayed watchlist.

    Maybe this can be expanded for the unfunctional movie details page atm

    Args:
        request (HttpRequest): The incoming AJAX POST request.
            Expects 'movie_id' in POST data.

    Returns:
        JsonResponse: Contains status ('success', 'error', 'not_found') and a 'message'.
    """
    movie_id_str = request.POST.get('movie_id')
    if not movie_id_str or not movie_id_str.isdigit():
        return JsonResponse({'status': 'error', 'message': 'Invalid Movie ID.'}, status=400)
    movie_id = int(movie_id_str)

    try:
        movie = get_object_or_404(Movie, tmdb_id=movie_id) # Ensure movie exists

    
        UserMovieInteraction.objects.filter(
            Q(interaction_type='watchlist') | Q(interaction_type='heart'),
            user=request.user,
            movie=movie,    
        ).delete()

         # This may be redundant, but fixes uniqueness conflict which crashed the page
        UserMovieInteraction.objects.update_or_create(
            user=request.user,
            movie=movie,
            interaction_type='skip',
            defaults={'timestamp': timezone.now()}
        )




        logger.info(f"Changed interaction type from 'watchlist' to 'skip' for movie {movie_id} ('{movie.title}') for user {request.user.id}")
        return JsonResponse({'status': 'success', 'message': 'Removed from watchlist successfully.'})
    except Movie.DoesNotExist:
        logger.error(f"Attempted to unwatchlist movie with TMDB ID {movie_id}, but Movie object does not exist locally. User: {request.user.id}")
        return JsonResponse({'status': 'error', 'message': 'Movie not found in database.'}, status=404)
    except UserMovieInteraction.DoesNotExist:
        # Was not found on user watchlist
        logger.warning(f"Attempted to remove movie {movie_id} from watchlist for user {request.user.id}, but no 'watchlist' interaction was found.")
        # Return success for UI consistency, as the item is effectively not on the watchlist, so ig it works
        return JsonResponse({'status': 'success', 'message': 'Movie was not on your watchlist.'})
    except Exception as e:
        logger.exception(f"Error during unwatchlist process for movie {movie_id}, user {request.user.id}: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)