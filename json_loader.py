"""
JSON Loader - Dynamic JSON loading and caching
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

class JSONLoader:
    """Loads and manages JSON files with caching"""
    
    def __init__(self, cache_ttl: int = 300):
        self.logger = logging.getLogger("nomi_json")
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.cache_timestamps = {}
        self.watch_files = {}
        
    async def load(self, file_path: str) -> Dict[str, Any]:
        """
        Load JSON file with caching
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
        """
        path = Path(file_path)
        
        # Check cache
        cache_key = str(path.absolute())
        if self._is_cached(cache_key):
            self.logger.debug(f"📦 Using cached: {file_path}")
            return self.cache[cache_key].copy()
            
        # Load from file
        try:
            if not path.exists():
                self.logger.warning(f"⚠️ JSON file not found: {file_path}")
                return {}
                
            # Read file
            async with asyncio.Lock():
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            # Update cache
            self.cache[cache_key] = data.copy()
            self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.debug(f"📄 Loaded JSON: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decode error in {file_path}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"❌ Error loading {file_path}: {e}")
            return {}
            
    async def save(self, file_path: str, data: Dict[str, Any]):
        """
        Save data to JSON file
        
        Args:
            file_path: Path to save
            data: Data to save
        """
        path = Path(file_path)
        
        try:
            # Create directory if not exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            async with asyncio.Lock():
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    
            # Update cache
            cache_key = str(path.absolute())
            self.cache[cache_key] = data.copy()
            self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.debug(f"💾 Saved JSON: {file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving {file_path}: {e}")
            
    async def watch_file(self, file_path: str, callback):
        """
        Watch JSON file for changes
        
        Args:
            file_path: Path to watch
            callback: Function to call on change
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.warning(f"⚠️ Cannot watch non-existent file: {file_path}")
            return
            
        # Calculate initial hash
        initial_hash = self._calculate_hash(file_path)
        self.watch_files[str(path.absolute())] = {
            'hash': initial_hash,
            'callback': callback,
            'path': path
        }
        
        self.logger.info(f"👁️ Watching file: {file_path}")
        
    async def check_watches(self):
        """Check all watched files for changes"""
        for file_info in self.watch_files.values():
            current_hash = self._calculate_hash(str(file_info['path']))
            
            if current_hash != file_info['hash']:
                self.logger.info(f"📝 File changed: {file_info['path'].name}")
                file_info['hash'] = current_hash
                
                # Clear cache for this file
                cache_key = str(file_info['path'].absolute())
                if cache_key in self.cache:
                    del self.cache[cache_key]
                    del self.cache_timestamps[cache_key]
                    
                # Call callback
                try:
                    await file_info['callback'](str(file_info['path']))
                except Exception as e:
                    self.logger.error(f"❌ Watch callback error: {e}")
                    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and valid"""
        if cache_key not in self.cache:
            return False
            
        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False
            
        age = datetime.now() - timestamp
        return age.total_seconds() < self.cache_ttl
        
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
            
    def clear_cache(self, file_path: Optional[str] = None):
        """Clear cache"""
        if file_path:
            cache_key = str(Path(file_path).absolute())
            if cache_key in self.cache:
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]
                self.logger.debug(f"🧹 Cleared cache for: {file_path}")
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
            self.logger.debug("🧹 Cleared all cache")
            
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            'cache_size': len(self.cache),
            'watched_files': len(self.watch_files),
            'cache_hits': sum(1 for key in self.cache if self._is_cached(key))
        }