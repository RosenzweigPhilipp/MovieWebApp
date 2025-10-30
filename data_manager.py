import os
import requests
from dotenv import load_dotenv
from models import db, User, Movie

# Load environment variables from .env file
load_dotenv()


class DataManager:
    """
    Data Manager class for handling CRUD operations on User and Movie models
    using SQLAlchemy ORM.
    """
    
    def __init__(self):
        """Initialize DataManager with OMDb API configuration."""
        self.omdb_api_key = os.getenv('OMDB_API_KEY')
        self.omdb_base_url = os.getenv('OMDB_BASE_URL', 'http://www.omdbapi.com/')
    
    def fetch_movie_data(self, title):
        """
        Fetch movie data from OMDb API.
        
        Args:
            title (str): The title of the movie to search for
        
        Returns:
            dict: Movie data from OMDb API, or None if not found or error occurred
        """
        if not self.omdb_api_key:
            print("Warning: OMDb API key not found in environment variables")
            return None
        
        try:
            # Prepare API request parameters
            params = {
                'apikey': self.omdb_api_key,
                't': title,  # Search by title
                'plot': 'short'  # Get short plot summary
            }
            
            # Make API request
            response = requests.get(self.omdb_base_url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Check if movie was found
            if data.get('Response') == 'True':
                return data
            else:
                print(f"Movie not found in OMDb: {data.get('Error', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from OMDb API: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def create_user(self, name):
        """
        Add a new user to the database.
        
        Args:
            name (str): The name of the user to create
        
        Returns:
            User: The created user object
        """
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user
    
    def get_users(self):
        """
        Return a list of all users in the database.
        
        Returns:
            list: List of all User objects
        """
        return User.query.all()
    
    def get_movies(self, user_id):
        """
        Return a list of all movies for a specific user.
        
        Args:
            user_id (int): The ID of the user whose movies to retrieve
        
        Returns:
            list: List of Movie objects belonging to the user
        """
        return Movie.query.filter_by(user_id=user_id).all()
    
    def add_movie(self, title, user_id):
        """
        Add a new movie to a user's favorites by fetching data from OMDb API.
        
        Args:
            title (str): The title of the movie to add
            user_id (int): The ID of the user adding the movie
        
        Returns:
            Movie: The created movie object with OMDb data, or None if movie not found
        """
        # Fetch movie data from OMDb API
        omdb_data = self.fetch_movie_data(title)
        
        if not omdb_data:
            # If OMDb data not available, create movie with just title
            new_movie = Movie(
                title=title,
                user_id=user_id
            )
        else:
            # Extract data from OMDb response and convert to appropriate types
            year = None
            if omdb_data.get('Year') and omdb_data['Year'] != 'N/A':
                try:
                    year = int(omdb_data['Year'])
                except (ValueError, TypeError):
                    year = None
            
            rating = None
            if omdb_data.get('imdbRating') and omdb_data['imdbRating'] != 'N/A':
                try:
                    rating = float(omdb_data['imdbRating'])
                except (ValueError, TypeError):
                    rating = None
            
            genre = omdb_data.get('Genre', None)
            if genre == 'N/A':
                genre = None
            
            # Create movie object with OMDb data
            new_movie = Movie(
                title=omdb_data.get('Title', title),  # Use OMDb title or fallback to search title
                year=year,
                genre=genre,
                rating=rating,
                user_id=user_id
            )
        
        # Save to database
        db.session.add(new_movie)
        db.session.commit()
        return new_movie
    
    def add_movie_object(self, movie):
        """
        Add a Movie object directly to the database (for backward compatibility).
        
        Args:
            movie (Movie): A Movie object to add to the database
        
        Returns:
            Movie: The created movie object
        """
        db.session.add(movie)
        db.session.commit()
        return movie
    
    def update_movie(self, movie_id, new_title):
        """
        Update the title of a specific movie in the database.
        
        Args:
            movie_id (int): The ID of the movie to update
            new_title (str): The new title for the movie
        
        Returns:
            Movie: The updated movie object, or None if not found
        """
        movie = Movie.query.get(movie_id)
        if movie:
            movie.title = new_title
            db.session.commit()
            return movie
        return None
    
    def delete_movie(self, movie_id):
        """
        Delete a movie from the user's list of favorites.
        
        Args:
            movie_id (int): The ID of the movie to delete
        
        Returns:
            bool: True if deletion was successful, False if movie not found
        """
        movie = Movie.query.get(movie_id)
        if movie:
            db.session.delete(movie)
            db.session.commit()
            return True
        return False