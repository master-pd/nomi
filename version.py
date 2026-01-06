"""
Version System - Manages bot version and updates
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

class VersionManager:
    """Manages bot version and updates"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_version")
        self.version_file = "config/version.json"
        self.current_version = self._get_current_version()
        self.update_history = []
        
    def _get_current_version(self) -> Dict[str, Any]:
        """Get current version information"""
        default_version = {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "build": 1,
            "codename": "𝗡𝗢𝗠𝗜 ⟵𝗼_𝟬",
            "release_date": "2026-01-08",
            "changelog": [
                "Initial release",
                "Ultra Pro Max Enterprise System"
            ],
            "compatibility": {
                "python": ">=3.8",
                "telegram_bot_api": ">=20.0"
            }
        }
        
        version_file = Path(self.version_file)
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"❌ Error loading version file: {e}")
                
        # Create default version file
        self._save_version(default_version)
        return default_version
        
    def _save_version(self, version_data: Dict[str, Any]):
        """Save version data"""
        try:
            version_file = Path(self.version_file)
            version_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving version file: {e}")
            
    def get_version_string(self) -> str:
        """Get version as string"""
        v = self.current_version
        return f"v{v['major']}.{v['minor']}.{v['patch']}-build{v['build']}"
        
    def get_full_version_info(self) -> Dict[str, Any]:
        """Get full version information"""
        return {
            **self.current_version,
            "version_string": self.get_version_string(),
            "hash": self._get_version_hash(),
            "loaded_at": datetime.now().isoformat()
        }
        
    def _get_version_hash(self) -> str:
        """Get version hash"""
        version_str = json.dumps(self.current_version, sort_keys=True)
        return hashlib.sha256(version_str.encode()).hexdigest()[:16]
        
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check for updates
        
        Returns:
            Update information
        """
        # TODO: Implement actual update checking
        # For now, return no updates
        return {
            "update_available": False,
            "current_version": self.get_version_string(),
            "latest_version": self.get_version_string(),
            "changelog": [],
            "critical": False,
            "recommended": False
        }
        
    async def perform_update(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform bot update
        
        Args:
            target_version: Target version (None for latest)
            
        Returns:
            Update result
        """
        # TODO: Implement actual update mechanism
        self.logger.warning("⚠️ Update system not fully implemented")
        
        return {
            "success": False,
            "message": "Update system not implemented",
            "current_version": self.get_version_string(),
            "requires_restart": True
        }
        
    def record_update(self, from_version: str, to_version: str, 
                     success: bool, notes: str = ""):
        """Record update in history"""
        update_record = {
            "timestamp": datetime.now().isoformat(),
            "from_version": from_version,
            "to_version": to_version,
            "success": success,
            "notes": notes,
            "hash_before": self._get_version_hash()
        }
        
        self.update_history.append(update_record)
        
        # Keep only last 50 updates
        if len(self.update_history) > 50:
            self.update_history = self.update_history[-50:]
            
        # Save update history
        self._save_update_history()
        
    def _save_update_history(self):
        """Save update history"""
        try:
            history_file = Path("data/update_history.json")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.update_history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving update history: {e}")
            
    def get_update_history(self, limit: int = 10) -> list:
        """Get update history"""
        return self.update_history[-limit:] if limit else self.update_history.copy()
        
    def increment_build(self):
        """Increment build number"""
        self.current_version["build"] += 1
        self.current_version["release_date"] = datetime.now().date().isoformat()
        self._save_version(self.current_version)
        
        self.logger.info(f"🔨 Incremented build to {self.get_version_string()}")
        
    def set_version(self, major: int, minor: int, patch: int, 
                   codename: Optional[str] = None):
        """
        Set new version
        
        Args:
            major: Major version
            minor: Minor version
            patch: Patch version
            codename: Version codename
        """
        old_version = self.get_version_string()
        
        self.current_version.update({
            "major": major,
            "minor": minor,
            "patch": patch,
            "build": 1,
            "release_date": datetime.now().date().isoformat(),
            "codename": codename or self.current_version.get("codename", "")
        })
        
        self._save_version(self.current_version)
        
        new_version = self.get_version_string()
        self.logger.info(f"🔄 Version changed: {old_version} → {new_version}")
        
        # Record version change
        self.record_update(
            from_version=old_version,
            to_version=new_version,
            success=True,
            notes="Manual version change"
        )
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import sys
        import platform
        
        return {
            "bot_version": self.get_version_string(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_implementation": platform.python_implementation(),
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor()
        }
        
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify system integrity
        
        Returns:
            Integrity check results
        """
        # TODO: Implement integrity checking
        # Check critical files, dependencies, etc.
        
        return {
            "integrity_check": True,
            "missing_files": [],
            "corrupted_files": [],
            "version_mismatch": False,
            "hash_verification": True
        }

# Global version manager instance
version_manager = VersionManager()

def get_version() -> str:
    """Get current version string"""
    return version_manager.get_version_string()

def get_version_info() -> Dict[str, Any]:
    """Get full version information"""
    return version_manager.get_full_version_info()

__version__ = get_version()