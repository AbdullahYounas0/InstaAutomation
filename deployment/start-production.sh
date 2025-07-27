#!/bin/bash

# Production startup script
APP_DIR="/var/www/insta-automation"
VENV_DIR="$APP_DIR/venv"

cd $APP_DIR/backend
source $VENV_DIR/bin/activate

# Load environment variables
if [ -f "$APP_DIR/.env" ]; then
    export $(cat $APP_DIR/.env | xargs)
fi

# Start gunicorn
exec gunicorn --config gunicorn.conf.py app:app
