#!/bin/sh
python app.py &
sleep 3
python test_app.py
