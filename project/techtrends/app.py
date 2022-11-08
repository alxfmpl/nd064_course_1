import logging
import random
import sqlite3

from flask import (
    Flask,
    jsonify,
    json,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    connection.close()
    return post


# Function to get a post count
def post_count():
    connection = get_db_connection()
    post_count = connection.execute("SELECT COUNT(*) FROM posts").fetchone()
    connection.close()
    return post_count[0]


# Function that returns simulated active connections
def db_connection_count():
    return random.randint(0, 100)


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"
app.logger.setLevel(logging.DEBUG)

# Define the main route of the web application
@app.route("/")
def index():
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()
    return render_template("index.html", posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info(f"A non-existing articel was accessed with post ID {post_id}")
        return render_template("404.html"), 404
    else:
        app.logger.info(f"Article \"{post['title']}\" retrieved!")
        return render_template("post.html", post=post)


# Define the About Us page
@app.route("/about")
def about():
    app.logger.info(f'The "About" page was accessed')
    return render_template("about.html")


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            connection.commit()
            connection.close()
            app.logger.info(f'A new article was created with title "{title}"')
            return redirect(url_for("index"))

    return render_template("create.html")


# Define a healthcheck endpoint
@app.route("/healthz")
def healthz():
    try:
        connection = get_db_connection()
    except:
        return {"result": "ERROR - unhealthy"}, 500

    try:
        if (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='posts'"
            ).fetchone()
            is None
        ):
            raise ValueError("Posts table does not exist in database")
    except ValueError:
        return {"result": "ERROR - unhealthy"}, 500

    return {"result": "OK - healthy"}, 200


# Define metrics endpoint
@app.route("/metrics")
def metrics():
    db_connection_count = db_connection_count()
    post_count = post_count()
    metrics = {"db_connection_count": db_connection_count, "post_count": post_count}
    return metrics, 200


# start the application on port 3111
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3111")
