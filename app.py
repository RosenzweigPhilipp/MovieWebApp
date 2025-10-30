import os
from flask import Flask, request, redirect, url_for, render_template, flash
from data_manager import DataManager
from models import db, Movie

app = Flask(__name__)

# Configure Flask
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a random secret key in production

# Configure SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link the database and the app
db.init_app(app)

# Create an object of DataManager class
data_manager = DataManager()


def validate_user_input(name):
    """Validate user input for creating users."""
    if not name:
        raise ValueError("User name cannot be empty")
    if len(name.strip()) < 2:
        raise ValueError("User name must be at least 2 characters long")
    if len(name.strip()) > 100:
        raise ValueError("User name cannot be longer than 100 characters")
    return name.strip()


def validate_movie_input(title):
    """Validate user input for creating movies."""
    if not title:
        raise ValueError("Movie title cannot be empty")
    if len(title.strip()) < 1:
        raise ValueError("Movie title must be at least 1 character long")
    if len(title.strip()) > 200:
        raise ValueError("Movie title cannot be longer than 200 characters")
    return title.strip()


def get_user_by_id(user_id):
    """Get user by ID with proper error handling."""
    try:
        users = data_manager.get_users()
        user = next((u for u in users if u.id == user_id), None)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user
    except Exception as e:
        raise Exception(f"Error fetching user: {str(e)}")


@app.route('/')
def index():
    """Home page showing all users and form for adding new users."""
    users = data_manager.get_users()
    
    # Calculate movie counts for each user and total
    user_movie_counts = {}
    total_movies = 0
    
    for user in users:
        movie_count = len(data_manager.get_movies(user.id))
        user_movie_counts[user.id] = movie_count
        total_movies += movie_count
    
    return render_template('index.html', 
                         users=users, 
                         user_movie_counts=user_movie_counts,
                         total_movies=total_movies)


@app.route('/users', methods=['POST'])
def create_user():
    """Handle adding a new user via POST request."""
    try:
        # Validate input
        raw_name = request.form.get('name', '')
        name = validate_user_input(raw_name)
        
        # Check if user already exists
        existing_users = data_manager.get_users()
        if any(user.name.lower() == name.lower() for user in existing_users):
            flash(f'User "{name}" already exists!', 'error')
            return redirect(url_for('index'))
        
        # Create user
        data_manager.create_user(name)
        flash(f'User "{name}" added successfully!', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('An unexpected error occurred while creating the user.', 'error')
        print(f"Error creating user: {str(e)}")
    
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_movies(user_id):
    """Display a specific user's favorite movies."""
    try:
        # Validate user exists
        user = get_user_by_id(user_id)
        
        # Get movies for the user
        movies = data_manager.get_movies(user_id)
        
        return render_template('movies.html', user=user, movies=movies)
    
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash('An error occurred while loading the movies.', 'error')
        print(f"Error loading movies for user {user_id}: {str(e)}")
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """Add a new movie to a user's favorites with OMDb data."""
    raw_title = request.form.get('title', '')  # Initialize at the start
    
    try:
        # Validate user exists
        user = get_user_by_id(user_id)
        
        # Validate movie input
        title = validate_movie_input(raw_title)
        
        # Check if movie already exists for this user
        existing_movies = data_manager.get_movies(user_id)
        if any(movie.title.lower() == title.lower() for movie in existing_movies):
            flash(f'Movie "{title}" is already in your collection!', 'error')
            return redirect(url_for('get_movies', user_id=user_id))
        
        # Add the movie
        movie = data_manager.add_movie(title, user_id)
        if movie:
            flash(f'Movie "{title}" added successfully!', 'success')
        else:
            flash(f'Movie "{title}" added, but OMDb data not found.', 'warning')
            
    except ValueError as e:
        flash(str(e), 'error')
    except ConnectionError:
        flash('Network error: Could not fetch movie data. Movie added with basic information.', 'warning')
    except Exception as e:
        flash('An unexpected error occurred while adding the movie.', 'error')
        print(f"Error adding movie '{raw_title}' for user {user_id}: {str(e)}")
    
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """Update the title of a specific movie."""
    raw_title = request.form.get('title', '')
    
    try:
        # Validate user exists
        user = get_user_by_id(user_id)
        
        # Validate movie input
        new_title = validate_movie_input(raw_title)
        
        # Update the movie
        movie = data_manager.update_movie(movie_id, new_title)
        if movie:
            flash(f'Movie updated to "{new_title}" successfully!', 'success')
        else:
            flash('Movie not found!', 'error')
            
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('An unexpected error occurred while updating the movie.', 'error')
        print(f"Error updating movie {movie_id} for user {user_id}: {str(e)}")
    
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Delete a specific movie from user's favorites."""
    try:
        # Validate user exists
        user = get_user_by_id(user_id)
        
        # Get movie title before deletion for the flash message
        movies = data_manager.get_movies(user_id)
        movie = next((m for m in movies if m.id == movie_id), None)
        
        if not movie:
            flash('Movie not found!', 'error')
            return redirect(url_for('get_movies', user_id=user_id))
        
        movie_title = movie.title
        
        # Delete the movie
        success = data_manager.delete_movie(movie_id)
        if success:
            flash(f'Movie "{movie_title}" deleted successfully!', 'success')
        else:
            flash('Failed to delete movie!', 'error')
            
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('An unexpected error occurred while deleting the movie.', 'error')
        print(f"Error deleting movie {movie_id} for user {user_id}: {str(e)}")
    
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user and all their movies."""
    try:
        users = data_manager.get_users()
        user = next((u for u in users if u.id == user_id), None)
        
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('index'))
        
        user_name = user.name
        
        # Delete all movies for this user first
        movies = data_manager.get_movies(user_id)
        for movie in movies:
            data_manager.delete_movie(movie.id)
        
        # Delete the user (Note: This would require adding delete_user method to DataManager)
        # For now, we'll just show a message
        flash(f'Note: User deletion not yet implemented. User "{user_name}" still exists.', 'warning')
        
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors with a custom page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors with a custom page."""
    # Rollback any database changes in case of error
    db.session.rollback()
    return render_template('500.html'), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions gracefully."""
    # Log the error (in production, you'd use proper logging)
    print(f"Unexpected error: {str(error)}")
    
    # Rollback any database changes
    db.session.rollback()
    
    # Check if it's an HTTP error (has a code)
    if hasattr(error, 'code'):
        if error.code == 404:
            return render_template('404.html'), 404
        else:
            return render_template('500.html'), error.code
    
    # For all other exceptions, return 500
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)