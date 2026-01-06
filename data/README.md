# Data Directory

This directory contains all dynamic data for the NOMI bot.

## Structure

data/
├── cache/           # Temporary cache files
│   ├── images/      # Generated images
│   ├── voice/       # Generated voice files
│   └── json/        # Cached JSON data
├── logs/           # Log files
│   ├── bot.log     # Main log file
│   ├── errors.log  # Error logs
│   └── audit.log   # Audit logs
├── stats/          # Statistics data
│   └── usage.json  # Usage statistics
├── backups/        # Backup files
│   └── auto/       # Automatic backups
└── nomi.db        # SQLite database

## Backup

- Automatic backups are stored in data/backups/auto/
- Manual backups can be created with /backup command
- Backups include database and configuration

## Cleanup

- Cache files are automatically cleaned up
- Old log files are rotated
- Expired data is removed automatically
