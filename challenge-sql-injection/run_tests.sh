#!/bin/sh

# Start the student's flask application in the background
echo "Starting Flask server..."
python app.py &

# Wait for a few seconds to ensure the server is up
sleep 3

# Run the tests
echo "Running tests..."
python test_app.py

# The exit code of the container will be the exit code of the test script