from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config')

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .seed import seed_command
    app.cli.add_command(seed_command)

    return app
