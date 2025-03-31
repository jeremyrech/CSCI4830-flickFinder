from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserFilter

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class FilterForm(forms.ModelForm):
    class Meta:
        model = UserFilter
        fields = ['genre_ids', 'min_release_year', 'max_release_year', 'min_rating']
        widgets = {
            'genre_ids': forms.CheckboxSelectMultiple(),
            'min_release_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'max_release_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'min_rating': forms.NumberInput(attrs={'min': 0, 'max': 10, 'step': 0.5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .services.tmdb_service import TMDBService
        
        # Get genres from TMDB
        tmdb_service = TMDBService()
        genres = tmdb_service.get_genre_list()
        
        # Create choices for genre field
        genre_choices = [(str(genre['id']), genre['name']) for genre in genres]
        self.fields['genre_ids'].widget.choices = genre_choices