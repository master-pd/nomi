#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/your_crush_bot/$DATE"

mkdir -p $BACKUP_DIR

# Backup database files
cp -r /opt/your_crush_bot/db $BACKUP_DIR/

# Backup logs
cp -r /opt/your_crush_bot/logs $BACKUP_DIR/

# Backup configuration
cp /opt/your_crush_bot/config.py $BACKUP_DIR/
cp /opt/your_crush_bot/.env $BACKUP_DIR/

# Create archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR

# Remove temporary directory
rm -rf $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"

# Remove backups older than 30 days
find /backup/your_crush_bot -name "*.tar.gz" -mtime +30 -delete