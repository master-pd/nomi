"""
Config Loader - Loads and manages bot configuration
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class BotMode(Enum):
    """Bot operation modes"""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"

@dataclass
class BotConfig:
    """Bot configuration dataclass"""
    name: str = "𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬"
    version: str = "1.0.0"
    language: str = "bn"
    timezone: str = "Asia/Dhaka"
    mode: BotMode = BotMode.PRODUCTION
    debug: bool = False
    admin_ids: list = None
    
    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = []

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    path: str = "data/nomi.db"
    backup_interval: int = 3600
    max_connections: int = 10
    
@dataclass
class APIConfig:
    """API configuration"""
    telegram_token: str = ""
    openweather_key: str = ""
    google_api_key: str = ""
    
@dataclass
class CacheConfig:
    """Cache configuration"""
    json_ttl: int = 300
    voice_ttl: int = 600
    image_ttl: int = 600
    max_size_mb: int = 100
    
@dataclass
class PerformanceConfig:
    """Performance configuration"""
    max_workers: int = 10
    queue_size: int = 1000
    timeout: int = 30
    retry_attempts: int = 3

class ConfigLoader:
    """Loads and manages all configurations"""
    
    def __init__(self, config_dir: str = "config"):
        self.logger = logging.getLogger("nomi_config")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.bot_config: Optional[BotConfig] = None
        self.db_config: Optional[DatabaseConfig] = None
        self.api_config: Optional[APIConfig] = None
        self.cache_config: Optional[CacheConfig] = None
        self.perf_config: Optional[PerformanceConfig] = None
        
    async def load_all(self):
        """Load all configurations"""
        self.logger.info("📋 Loading configurations...")
        
        # Load bot config
        await self._load_bot_config()
        
        # Load database config
        await self._load_db_config()
        
        # Load API config
        await self._load_api_config()
        
        # Load cache config
        await self._load_cache_config()
        
        # Load performance config
        await self._load_perf_config()
        
        self.logger.info("✅ All configurations loaded")
        
    async def _load_bot_config(self):
        """Load bot configuration"""
        config_file = self.config_dir / "bot.json"
        
        if not config_file.exists():
            # Create default
            self.bot_config = BotConfig()
            await self._save_bot_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convert mode string to enum
                if 'mode' in data:
                    data['mode'] = BotMode(data['mode'])
                    
                self.bot_config = BotConfig(**data)
                
            except Exception as e:
                self.logger.error(f"❌ Error loading bot config: {e}")
                self.bot_config = BotConfig()
                
    async def _load_db_config(self):
        """Load database configuration"""
        config_file = self.config_dir / "database.json"
        
        if not config_file.exists():
            self.db_config = DatabaseConfig()
            await self._save_db_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.db_config = DatabaseConfig(**data)
            except Exception as e:
                self.logger.error(f"❌ Error loading DB config: {e}")
                self.db_config = DatabaseConfig()
                
    async def _load_api_config(self):
        """Load API configuration"""
        config_file = self.config_dir / "api_keys.json"
        
        if not config_file.exists():
            self.api_config = APIConfig()
            await self._save_api_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.api_config = APIConfig(**data)
            except Exception as e:
                self.logger.error(f"❌ Error loading API config: {e}")
                self.api_config = APIConfig()
                
    async def _load_cache_config(self):
        """Load cache configuration"""
        config_file = self.config_dir / "cache.json"
        
        if not config_file.exists():
            self.cache_config = CacheConfig()
            await self._save_cache_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.cache_config = CacheConfig(**data)
            except Exception as e:
                self.logger.error(f"❌ Error loading cache config: {e}")
                self.cache_config = CacheConfig()
                
    async def _load_perf_config(self):
        """Load performance configuration"""
        config_file = self.config_dir / "performance.json"
        
        if not config_file.exists():
            self.perf_config = PerformanceConfig()
            await self._save_perf_config()
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.perf_config = PerformanceConfig(**data)
            except Exception as e:
                self.logger.error(f"❌ Error loading perf config: {e}")
                self.perf_config = PerformanceConfig()
                
    async def _save_bot_config(self):
        """Save bot configuration"""
        if self.bot_config:
            config_file = self.config_dir / "bot.json"
            data = asdict(self.bot_config)
            data['mode'] = data['mode'].value  # Convert enum to string
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
    async def save_all(self):
        """Save all configurations"""
        await self._save_bot_config()
        await self._save_db_config()
        await self._save_api_config()
        await self._save_cache_config()
        await self._save_perf_config()
        
    async def _save_db_config(self):
        """Save database configuration"""
        if self.db_config:
            config_file = self.config_dir / "database.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.db_config), f, indent=2, ensure_ascii=False)
                
    async def _save_api_config(self):
        """Save API configuration"""
        if self.api_config:
            config_file = self.config_dir / "api_keys.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.api_config), f, indent=2, ensure_ascii=False)
                
    async def _save_cache_config(self):
        """Save cache configuration"""
        if self.cache_config:
            config_file = self.config_dir / "cache.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.cache_config), f, indent=2, ensure_ascii=False)
                
    async def _save_perf_config(self):
        """Save performance configuration"""
        if self.perf_config:
            config_file = self.config_dir / "performance.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.perf_config), f, indent=2, ensure_ascii=False)
                
    def get_bot_config(self) -> BotConfig:
        """Get bot configuration"""
        if not self.bot_config:
            raise RuntimeError("Bot config not loaded")
        return self.bot_config
        
    def get_db_config(self) -> DatabaseConfig:
        """Get database configuration"""
        if not self.db_config:
            raise RuntimeError("DB config not loaded")
        return self.db_config
        
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        if not self.api_config:
            raise RuntimeError("API config not loaded")
        return self.api_config
        
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        if not self.cache_config:
            raise RuntimeError("Cache config not loaded")
        return self.cache_config
        
    def get_perf_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        if not self.perf_config:
            raise RuntimeError("Perf config not loaded")
        return self.perf_config
        
    def update_bot_config(self, **kwargs):
        """Update bot configuration"""
        if not self.bot_config:
            self.bot_config = BotConfig()
            
        for key, value in kwargs.items():
            if hasattr(self.bot_config, key):
                setattr(self.bot_config, key, value)
                
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        if not self.bot_config:
            return False
        return user_id in self.bot_config.admin_ids