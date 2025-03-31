import requests
from django.conf import settings
from ..models import Movie

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self):
        # We will need to switch this to that environment variable thing too I think
        self.api_key = settings.TMDB_API_KEY
    
    def _make_request(self, endpoint, params=None):
        """Make a request to the TMDB API"""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Log error and return empty dict
            print(f"Error {response.status_code}: {response.text}")
            return {}
    
    def discover_movies(self, filters=None, page=1):
        """Gets list of movies based on filters"""
        params = {'page': page}
        
        if filters:
            if filters.genre_ids:
                params['with_genres'] = ','.join(filters.genre_ids)
            
            if filters.min_release_year:
                params['primary_release_date.gte'] = f"{filters.min_release_year}-01-01"
            
            if filters.max_release_year:
                params['primary_release_date.lte'] = f"{filters.max_release_year}-12-31"
            
            if filters.min_rating:
                params['vote_average.gte'] = filters.min_rating
        
        # Add random sorting to get variety
        # Maybe later we can add some sort of probability curve to recommend higher rated
        params['sort_by'] = 'popularity.desc'
        
        data = self._make_request("discover/movie", params)
        return data.get('results', [])
    
    def get_movie_details(self, movie_id):
        """Get information about a specific movie"""
        data = self._make_request(f"movie/{movie_id}")
        return data
    
    def get_or_create_movie(self, tmdb_movie_data):
        """Create or update a movie in the sqlite django thing from TMDB data"""
        # Have ideas for created later, added it here so I don't forget
        movie, created = Movie.objects.get_or_create(
            tmdb_id=tmdb_movie_data['id'],
            defaults={
                'title': tmdb_movie_data['title'],
                'poster_path': tmdb_movie_data.get('poster_path'),
                'overview': tmdb_movie_data.get('overview'),
                'release_date': tmdb_movie_data.get('release_date'),
            }
        )
        
        return movie
    
    def get_genre_list(self):
        """Get list of available genres"""
        data = self._make_request("genre/movie/list")
        return data.get('genres', [])
