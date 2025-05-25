import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from .models import *
from . import db

@click.command('seed')
@with_appcontext
def seed_command():
    universities = [
        {
            "name": "Northwestern University"
        },
        {
            "name": "University of Maryland"
        }
    ]

    companies = [
        {
            "name": "Google"
        },
        {
            "name": "Microsoft"
        },
        {
            "name": "Netflix"
        },
        {
            "name": "Blackstone"
        },
        {
            "name": "Apple"
        }
    ]

    db.session.add_all([University(**u) for u in universities])
    db.session.add_all([Company(**c) for c in companies])
    db.session.commit()
    print("Seeded sample data.")
