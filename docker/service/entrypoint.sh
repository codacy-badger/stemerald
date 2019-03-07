#!/bin/sh

gunicorn -w 4 --bind localhost:8080 'wsgi:app'
