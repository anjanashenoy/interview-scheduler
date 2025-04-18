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
            "name": "Northwestern University",
            "phone": "847-491-3741",
            "address": "633 Clark St, Evanston, IL 60208"
        },
        {
            "name": "University of Maryland",
            "phone": "301-405-1000",
            "address": "College Park, MD 20742"
        }
    ]

    companies = [
        {
            "name": "TechNova Inc",
            "phone": "312-555-0198",
            "address": "500 W Madison St, Chicago, IL 60661"
        },
        {
            "name": "GreenByte Solutions",
            "phone": "415-555-2323",
            "address": "22 Market St, San Francisco, CA 94103"
        },
        {
            "name": "QuantumSoft",
            "phone": "212-555-0071",
            "address": "88 Wall St, New York, NY 10005"
        },
        {
            "name": "NeuralEdge AI",
            "phone": "206-555-3210",
            "address": "1200 5th Ave, Seattle, WA 98101"
        },
        {
            "name": "CloudBridge Corp",
            "phone": "617-555-8844",
            "address": "200 Cambridge Park Dr, Cambridge, MA 02140"
        }
    ]

    db.session.add_all([University(**u) for u in universities])
    db.session.add_all([Company(**c) for c in companies])
    db.session.commit()
    print("Seeded sample data.")
