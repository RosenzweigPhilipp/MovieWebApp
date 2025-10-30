import os
from flask import Flask, request, redirect, url_for
from data_manager import DataManager
from models import db, Movie

app = Flask(__name__)

# Configure SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link the database and the app
db.init_app(app)

# Create an object of DataManager class
data_manager = DataManager()


@app.route('/')
def home():
    """Home page showing all users and form for adding new users."""
    users = data_manager.get_users()
    # For now, return simple HTML with user list and add user form
    users_html = "<h2>Users:</h2><ul>"
    for user in users:
        users_html += f'<li><a href="/users/{user.id}/movies">{user.name}</a></li>'
    users_html += "</ul>"
    
    add_user_form = """
    <h3>Add New User:</h3>
    <form method="POST" action="/users">
        <input type="text" name="name" placeholder="User Name" required>
        <button type="submit">Add User</button>
    </form>
    """
    
    return f"<h1>Welcome to MoviWeb App!</h1>{users_html}{add_user_form}"


@app.route('/users', methods=['POST'])
def add_user():
    """Handle adding a new user via POST request."""
    name = request.form.get('name')
    if name:
        data_manager.create_user(name)
    return redirect(url_for('home'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def user_movies(user_id):
    """Display a specific user's favorite movies."""
    movies = data_manager.get_movies(user_id)
    users = data_manager.get_users()
    user = next((u for u in users if u.id == user_id), None)
    
    if not user:
        return f"User with ID {user_id} not found!", 404
    
    movies_html = f"<h2>{user.name}'s Favorite Movies:</h2>"
    
    if movies:
        movies_html += "<ul>"
        for movie in movies:
            movie_info = f"{movie.title}"
            if movie.year:
                movie_info += f" ({movie.year})"
            if movie.rating:
                movie_info += f" - Rating: {movie.rating}/10"
            if movie.genre:
                movie_info += f" - Genre: {movie.genre}"
            
            # Add update and delete buttons for each movie
            movies_html += f"""
            <li>
                {movie_info}
                <form style="display:inline;" method="POST" action="/users/{user_id}/movies/{movie.id}/update">
                    <input type="text" name="title" placeholder="New title" size="20">
                    <button type="submit">Update</button>
                </form>
                <form style="display:inline;" method="POST" action="/users/{user_id}/movies/{movie.id}/delete">
                    <button type="submit" onclick="return confirm('Are you sure?')">Delete</button>
                </form>
            </li>
            """
        movies_html += "</ul>"
    else:
        movies_html += "<p>No movies added yet.</p>"
    
    # Add movie form
    add_movie_form = f"""
    <h3>Add New Movie:</h3>
    <form method="POST" action="/users/{user_id}/movies">
        <input type="text" name="title" placeholder="Movie Title" required>
        <button type="submit">Add Movie</button>
    </form>
    <br><a href="/">← Back to Home</a>
    """
    
    return movies_html + add_movie_form


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """Add a new movie to a user's favorites with OMDb data."""
    title = request.form.get('title')
    if title:
        # The DataManager will fetch OMDb data automatically
        data_manager.add_movie(title, user_id)
    return redirect(url_for('user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """Update the title of a specific movie."""
    new_title = request.form.get('title')
    if new_title:
        data_manager.update_movie(movie_id, new_title)
    return redirect(url_for('user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Delete a specific movie from user's favorites."""
    data_manager.delete_movie(movie_id)
    return redirect(url_for('user_movies', user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)