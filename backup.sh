#!/bin/bash

# Backup script for Instagram Automation
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/backups"
PROJECT_DIR="/var/www/instagram-automation"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup user data and logs
tar -czf $BACKUP_DIR/instagram_automation_backup_$DATE.tar.gz \
    $PROJECT_DIR/backend/users.json \
    $PROJECT_DIR/backend/activity_logs.json \
    $PROJECT_DIR/backend/instagram_accounts.json \
    $PROJECT_DIR/backend/logs/ \
    $PROJECT_DIR/backend/.env

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t instagram_automation_backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: instagram_automation_backup_$DATE.tar.gz"
