#!/bin/bash

pip install -e .
flask --app flaskr init-db
flask --app flaskr run