## FlickFinder

FlickFinder is a Django-based web application hosted on AWS designed to simplify the challenging process of discovering new movies or rediscovering old classics. Through giving users an endless stack of cinema with the immediate option to either skip it or save it to a separate watchlist, it incorporates a user interface that is familiar while still being engaging. This watchlist feature gives ease towards saving intriguing titles, while on the opposite side each skipped movie will be saved to a list to temporarily block it from the user, which helps to prevent clutter and the frustration of repeatedly turning down specific movies that you might get from looking at a standard list of popular movies. 

The structure of the application highlights the principles of scalability, security, and reliability. To maintain integrity between the user and database, safeguards against SQL injections, HTTP header attacks, JS injections, and multiple others will be implemented as prime security measures. Both the frontend and backend codebases will be organized into well-documented functions to promote maintainability and to streamline collaboration via GitHub and Git.  

The current project scope takes advantage of free APIs and AWS trial instances in order to save on costs while providing the best user experience for those costs. Rate-limit constraints, along with enhancements such as filtering options and adaptive recommendations will be considered in the future as we adjust to the projected scope of the application. Overall FlickFinder's development process will demonstrate practical software engineering principles and collaborative teamwork in order to arrive at the optimal future deployment of the application to the user. 

## Requirements

```python
asgiref==3.8.1
Django==5.1.6
logging==0.4.9.6
requests==2.32.3
sqlparse==0.5.3
tzdata==2025.1
```

## Current Models

```python
UserProfile: (user)
Movie: <QuerySet [(tmdb_id, title, poster_path, overview, release_date, vote_average, vote_count, genres)>
UserMovieInteration: <QuerySet [(user, movie, interaction_type, timestamp)>
UserFilter: <QuerySet [(user, genre_ids, min_release_year, max_release_year, min_rating)]>
```

## Contributors

**Jeremy**

**Anhphat**

**Joe**

**Aiden**

**Will**

**Hekima**