"""
Bootstrap System - Initializes all components
"""

import asyncio
import json
from pathlib import Path
import logging

class Bootstrap:
    """Bootstraps the entire system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_bootstrap")
        self.modules = {}
        self.services = {}
        self.config = {}

    async def initialize(self):
        """Initialize all components"""
        self.logger.info("🔧 Initializing bootstrap system...")
        
        # Load configurations
        await self._load_configs()
        
        # Initialize directories
        await self._init_directories()
        
        # Load modules
        await self._load_modules()
        
        # Initialize services
        await self._init_services()
        
        self.logger.info("✅ Bootstrap completed!")

    async def _load_configs(self):
        """Load configuration files"""
        config_path = Path("config")
        config_path.mkdir(exist_ok=True)

        default_configs = {
            "bot.json": {
                "name": "𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬",
                "version": "1.0.0",
                "language": "bn",
                "timezone": "Asia/Dhaka",
                "admin_ids": [],
                "owner_id": None,
                "token": ""
            },
            "database.json": {
                "type": "sqlite",
                "path": "data/nomi.db",
                "backup_interval": 3600
            }
        }

        for filename, cfg in default_configs.items():
            path = config_path / filename
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
                self.logger.info(f"📝 Created {filename}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        self.config[filename] = json.load(f)
                    except json.JSONDecodeError:
                        self.logger.warning(f"⚠️ Invalid JSON in {filename}, using defaults")
                        self.config[filename] = cfg

    async def _init_directories(self):
        """Initialize required directories"""
        directories = [
            "assets/fonts",
            "assets/templates",
            "data/cache",
            "data/logs",
            "data/stats",
            "data/backups",
            "responses",
            "temp"
        ]
        for d in directories:
            Path(d).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"📁 Created directory: {d}")

    async def _load_modules(self):
        """Load all modules (placeholder)"""
        self.modules = {
            "welcome": None,
            "goodbye": None,
            "moderation": None,
            "voice": None,
            "image": None,
            "stats": None
        }

    async def _init_services(self):
        """Initialize background services"""
        self.services = {
            "scheduler": None,
            "cache": None,
            "monitor": None
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("🧹 Cleaning up resources...")

    def get_module(self, name: str):
        return self.modules.get(name)

    def get_service(self, name: str):
        return self.services.get(name)
