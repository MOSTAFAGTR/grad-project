#!/bin/sh

echo "Starting Flask server..."
python app.py &

sleep 3

echo "Running tests..."
python test_app.py
