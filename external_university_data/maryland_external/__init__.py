from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('external_university_data.maryland_external.config')

    db.init_app(app)
    Migrate(app, db)

    from . import models

    from .seed import seed_command
    app.cli.add_command(seed_command)

    return app
