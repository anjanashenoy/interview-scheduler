#!/bin/bash

pip install -e .
flask db upgrade
gunicorn flaskr:app --bind 0.0.0.0:$PORT