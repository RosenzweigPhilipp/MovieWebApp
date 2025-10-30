import os
from flask import Flask, request, redirect, url_for, render_template
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
def index():
    """Home page showing all users and form for adding new users."""
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def create_user():
    """Handle adding a new user via POST request."""
    name = request.form.get('name')
    if name:
        data_manager.create_user(name)
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_movies(user_id):
    """Display a specific user's favorite movies."""
    movies = data_manager.get_movies(user_id)
    users = data_manager.get_users()
    user = next((u for u in users if u.id == user_id), None)
    
    if not user:
        return f"User with ID {user_id} not found!", 404
    
    return render_template('movies.html', user=user, movies=movies)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """Add a new movie to a user's favorites with OMDb data."""
    title = request.form.get('title')
    if title:
        # The DataManager will fetch OMDb data automatically
        data_manager.add_movie(title, user_id)
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """Update the title of a specific movie."""
    new_title = request.form.get('title')
    if new_title:
        data_manager.update_movie(movie_id, new_title)
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """Delete a specific movie from user's favorites."""
    data_manager.delete_movie(movie_id)
    return redirect(url_for('get_movies', user_id=user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)