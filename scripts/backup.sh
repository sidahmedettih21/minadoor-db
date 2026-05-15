#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups
mkdir -p $BACKUP_DIR
PGPASSWORD=${DB_PASS} pg_dump -h db -U minadoor minadoordb > $BACKUP_DIR/minadoordb_$TIMESTAMP.sql
find $BACKUP_DIR -type f -mtime +7 -delete
