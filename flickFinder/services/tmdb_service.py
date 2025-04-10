import requests
import logging
from django.conf import settings
from ..models import Movie

logger = logging.getLogger(__name__) # Print bad for AWS, logger instead :D

class TMDBServiceError(Exception): # Trying funky exception handling
    pass

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self):
        # We will need to switch this to that environment variable thing too I think
        self.api_key = getattr(settings, 'TMDB_API_KEY', None)
        if not self.api_key:
            logger.error("TMDB_API_KEY not found in settings.")
            self.api_key = None

        self.session = requests.Session()
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the TMDB API"""
        if not self.api_key:
            # If API key wasn't loaded, log error and return None
            logger.error("TMDB API key is missing. Cannot make request.")
            return None

        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10) # temp timeout of 10
            response.raise_for_status() # raises errors, handled below
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"TMDB API request timed out for {url} after {self.REQUEST_TIMEOUT} seconds.")
            raise TMDBServiceError(f"API request timed out: {url}") from None
        except requests.exceptions.HTTPError as e:
             # Log specific HTTP errors
             logger.error(f"TMDB API HTTP error for {url}: Status={e.response.status_code}, Response={e.response.text[:200]}...")
             raise TMDBServiceError(f"API HTTP error {e.response.status_code} for {url}") from e
        except requests.exceptions.RequestException as e:
            # Catch other potential request errors
            logger.error(f"TMDB API request failed for {url}: {e}")
            raise TMDBServiceError(f"API request failed: {e}") from e
        except ValueError as e:
             logger.error(f"Failed to decode JSON response for {url}: {e}")
             raise TMDBServiceError(f"Invalid JSON response from {url}") from e

    
    def discover_movies(self, filters=None, page=1):
        """Gets list of movies based on filters"""
        params = {'page': page,
                  'sort_by': 'popularity.desc',
                  'include_adult': 'false',
                  'include_video': 'false',
                  'with_original_language': 'en',
                  'vote_count.gte': 200
        } # vote count prevents randoms
        
        if filters:
            genre_ids_list = getattr(filters, 'genre_ids', None)
            if isinstance(genre_ids_list, list) and genre_ids_list:
                # Filter out empty strings if any
                valid_genre_ids = [gid for gid in genre_ids_list if gid]
                if valid_genre_ids:
                    params['with_genres'] = ','.join(valid_genre_ids)
            
            min_year = getattr(filters, 'min_release_year', None)
            if min_year: params['primary_release_date.gte'] = f"{min_year}-01-01"

            max_year = getattr(filters, 'max_release_year', None)
            if max_year: params['primary_release_date.lte'] = f"{max_year}-12-31"

            min_rating = getattr(filters, 'min_rating', None)
            if min_rating: params['vote_average.gte'] = min_rating
        
        # Fetch movies from discovery endpoint
        try:
            data = self._make_request("discover/movie", params)
            if data:
                results = data.get('results', [])
                total_pages = min(data.get('total_pages', 0), 500)
                return results, total_pages
            else:
                return [], 0
        except TMDBServiceError:
            # Logged in _make_request, return empty list to calling function
             return [], 0
    
    def get_popular_movies(self, page=1):
        """Get popular movies without any filters"""
        params = {
            'page': page,
            'sort_by': 'popularity.desc',
            'include_adult': 'false',
            'include_video': 'false',
            'with_original_language': 'en',
            'vote_count.gte': 200
        }
        
        # Fetch movies from discovery endpoint
        try:
            data = self._make_request("discover/movie", params)
            if data:
                results = data.get('results', [])
                total_pages = min(data.get('total_pages', 0), 500)
                return results, total_pages
            else:
                return [], 0
        except TMDBServiceError:
            # Logged in _make_request, return empty list to calling function
             return [], 0
    
    def get_movie_details(self, movie_id):
        """Get information about a specific movie"""
        params = {'append_to_response': 'credits'} # get more details in details.html
        try:
            data = self._make_request(f"movie/{movie_id}", params=params)
            return data
        except TMDBServiceError:
            # Logged in _make_request
            return None
    
    def get_or_create_movie(self, tmdb_movie_data):
        """Create or update a movie in the sqlite django thing from TMDB data"""
        if not tmdb_movie_data or 'id' not in tmdb_movie_data:
             logger.warning("Attempted to get/create movie with invalid data.")
             return None # Return None if input data is bad
        
        try:
            movie, created = Movie.objects.get_or_create(
                tmdb_id=tmdb_movie_data['id'],
                defaults={
                    'title': tmdb_movie_data['title'],
                    'poster_path': tmdb_movie_data.get('poster_path'),
                    'overview': tmdb_movie_data.get('overview'),
                    'release_date': tmdb_movie_data.get('release_date') if tmdb_movie_data.get('release_date') else None,
                    'vote_average': tmdb_movie_data.get('vote_average'),
                    'vote_count': tmdb_movie_data.get('vote_count'),
                    'genres': tmdb_movie_data.get('genres', None) # this may be deleted, used for funky watchlist genre thing that may not work
                }
            )
            if created:
                logger.info(f"Created new movie in DB: {movie.title} (TMDB ID: {movie.tmdb_id})")
            if not movie.genres:
                logger.info(f"Genres missing for movie '{movie.title}' (TMDB ID: {movie.tmdb_id}). Fetching details...")
                try:
                    detailed_data = self.get_movie_details(movie.tmdb_id)
                    if detailed_data and 'genres' in detailed_data:
                        # Update the movie instance with the fetched genres
                        movie.genres = detailed_data.get('genres')
                        # Save only the updated fields to the db
                        movie.save(update_fields=['genres'])
                        logger.info(f"Successfully fetched and saved genres for movie '{movie.title}'.")
                    elif detailed_data:
                        logger.warning(f"Fetched details for movie '{movie.title}', but no 'genres' key found in response.")
                    else:
                        # This case handles if get_movie_details returned None (API error)
                        logger.error(f"Failed to fetch details for movie '{movie.title}' to get genres.")
                except TMDBServiceError as e:
                    logger.error(f"TMDB Service error while fetching details for genres: {e}")
                except Exception as e:
                    logger.exception(f"Unexpected error while fetching details for genres for movie '{movie.title}'")
            return movie

        except Exception as e:
            # Catch potential db errors during get_or_create
            logger.exception(f"Database error during get_or_create_movie for TMDB ID {tmdb_movie_data.get('id')}: {e}")
            return None
    
    def get_genre_list(self):
        """Get list of available genres"""
        try:
            data = self._make_request("genre/movie/list")
            return data.get('genres', []) if data else []
        except TMDBServiceError as e:
            return []