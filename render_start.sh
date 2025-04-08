#!/bin/bash

pip install -e .
gunicorn flaskr:app --bind 0.0.0.0:$PORT