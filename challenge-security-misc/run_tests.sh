#!/bin/sh
# We run app.py directly here because gunicorn overrides some debug flags
python app.py &
sleep 3
python test_app.py