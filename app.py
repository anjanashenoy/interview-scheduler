from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://default_j51m_user:nq9Q2w8oU8cbr7mo3t47mZs1exB1fdw1@dpg-cvqrqceuk2gs73c09k6g-a.virginia-postgres.render.com/default_j51m'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route('/')
def index():
    users = User.query.all()
    # Use a list comprehension to get user details in a readable format
    user_list = [f"ID: {user.id}, Username: {user.username}, Email: {user.email}" for user in users]
    return "<br>".join(user_list)  # Join the user details with line breaks for better readability
