#!/bin/sh


gunicorn -w 4 --bind 0.0.0.0:8080 'wsgi:app'
