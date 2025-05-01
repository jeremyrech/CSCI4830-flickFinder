## FlickFinder

FlickFinder is a Django-based web application hosted on AWS designed to simplify the challenging process of discovering new movies or rediscovering old classics. Through giving users an endless stack of cinema with the immediate option to either skip it or save it to a separate watchlist, it incorporates a user interface that is familiar while still being engaging. This watchlist feature gives ease towards saving intriguing titles, while on the opposite side each skipped movie will be saved to a list to temporarily block it from the user, which helps to prevent clutter and the frustration of repeatedly turning down specific movies that you might get from looking at a standard list of popular movies. 

The structure of the application highlights the principles of scalability, security, and reliability. To maintain integrity between the user and database, safeguards against SQL injections, HTTP header attacks, JS injections, and multiple others will be implemented as prime security measures. Both the frontend and backend codebases will be organized into well-documented functions to promote maintainability and to streamline collaboration via GitHub and Git.  

The current project scope takes advantage of free APIs and AWS trial instances in order to save on costs while providing the best user experience for those costs. Rate-limit constraints, along with enhancements such as filtering options and adaptive recommendations will be considered in the future as we adjust to the projected scope of the application. Overall FlickFinder's development process will demonstrate practical software engineering principles and collaborative teamwork in order to arrive at the optimal future deployment of the application to the user. 

## Installation
1. Download and install [Python](https://www.python.org/downloads/).
1. Download or clone the FlickFinder repository to any location on your machine.
1. Open the repository folder and create a `.env` file containing the Django secret key and [TMDB](https://www.themoviedb.org/) API key, using the following variables:
    <br>
    <br>
    ```bash
    # Django secret key
    SECRET_KEY = 'secret-key'

    # TMDB API key
    TMDB_API_KEY = 'api-key'
    ```
1. Open the repository folder in a common command-line environment. IDE programs like VS Code have terminals that may be used to run Command Prompt and Bash.
1. Depending on your shell, run either of the following scripts to set up the virtual environment and install all dependencies:
    - Command Prompt (Windows): `env.bat`
    - Zsh/Bash (Mac/Linux): `source env.sh`
1. Activate the virtual environment with the following command:
    - Command Prompt (Windows): `web_environment\Scripts\activate.bat`
    - Command Prompt (Windows): `source web_environment/bin/activate`

## Local Testing
1. To test FlickFinder locally, run the following Python commands:
    <br>
    <br>
    ```python
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
    ```
1. Visit the website at http://localhost:8000.

## Deployment (Linux only)
1. To deploy FlickFinder, run `source gunicorn-nginx.sh`. This script will do the following:
    - Disable debug mode
    - Set the allowed host in the Django settings
    - Configure and enable Gunicorn and Nginx
    - Collect Django static files
    - Make any pending migrations.
1. Open the host machine IP address in a web browser to visit the website.

## Current Models

```python
UserProfile: (user)
Movie: <QuerySet [(tmdb_id, title, poster_path, overview, release_date, vote_average, vote_count, genres)>
UserMovieInteration: <QuerySet [(user, movie, interaction_type, timestamp)>
UserFilter: <QuerySet [(user, genre_ids, min_release_year, max_release_year, min_rating)]>
```

## Contributors

**Jeremy**

**AnhPhat**

**Joe**

**Aiden**

**Will**

**Hekima**
