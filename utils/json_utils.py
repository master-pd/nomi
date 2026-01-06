"""
JSON Database Management System
Complete with CRUD operations, backups, and error handling
"""

import json
import os
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import hashlib
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)

class JSONManager:
    """Professional JSON database manager"""
    
    def __init__(self):
        self.users_file = Config.DB_USERS
        self.groups_file = Config.DB_GROUPS
        self.system_file = Config.DB_SYSTEM
        self.logs_file = Config.DB_LOGS
        
        # Initialize databases
        self._init_databases()
    
    def _init_databases(self):
        """Initialize all JSON databases"""
        databases = [
            (self.users_file, {"users": {}, "metadata": {"created": datetime.now().isoformat()}}),
            (self.groups_file, {"groups": {}, "metadata": {"created": datetime.now().isoformat()}}),
            (self.system_file, {"system": {}, "stats": {}, "settings": {}}),
            (self.logs_file, {"logs": [], "actions": [], "errors": []})
        ]
        
        for file_path, default_data in databases:
            self._ensure_file(file_path, default_data)
        
        logger.info("✅ All databases initialized")
    
    def _ensure_file(self, file_path: str, default_data: Dict):
        """Ensure JSON file exists with default data"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Created database file: {file_path}")
            else:
                # Validate existing file
                self._validate_json(file_path)
        except Exception as e:
            logger.error(f"Error ensuring file {file_path}: {e}")
            raise
    
    def _validate_json(self, file_path: str):
        """Validate JSON file structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic validation
            if not isinstance(data, dict):
                raise ValueError(f"Invalid JSON structure in {file_path}")
            
            return True
        except json.JSONDecodeError:
            logger.warning(f"Corrupted JSON file: {file_path}, creating backup and resetting")
            self._backup_file(file_path)
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def _backup_file(self, file_path: str):
        """Create backup of a file"""
        backup_dir = os.path.join(os.path.dirname(file_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, f"{filename}.backup_{timestamp}")
        
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
    
    def _read_json(self, file_path: str) -> Dict:
        """Read JSON file with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            self._backup_file(file_path)
            return {}
    
    def _write_json(self, file_path: str, data: Dict):
        """Write JSON file with error handling"""
        try:
            # Create backup before writing
            self._backup_file(file_path)
            
            # Write with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Verify write was successful
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise error if file is corrupted
            
            return True
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
            return False
    
    # ============ USER OPERATIONS ============
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data by ID"""
        data = self._read_json(self.users_file)
        return data.get("users", {}).get(str(user_id))
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        data = self._read_json(self.users_file)
        return list(data.get("users", {}).values())
    
    def update_user(self, user_id: int, user_data: Dict):
        """Update or create user data"""
        try:
            data = self._read_json(self.users_file)
            
            if "users" not in data:
                data["users"] = {}
            
            # Get existing data or create new
            existing = data["users"].get(str(user_id), {})
            
            # Merge with new data (new data has priority)
            updated_data = {**existing, **user_data, "last_updated": datetime.now().isoformat()}
            
            # Ensure required fields
            if "user_id" not in updated_data:
                updated_data["user_id"] = user_id
            if "created_at" not in updated_data:
                updated_data["created_at"] = datetime.now().isoformat()
            
            data["users"][str(user_id)] = updated_data
            
            # Update metadata
            data["metadata"] = {
                **data.get("metadata", {}),
                "last_updated": datetime.now().isoformat(),
                "total_users": len(data["users"])
            }
            
            success = self._write_json(self.users_file, data)
            
            if success:
                logger.debug(f"Updated user: {user_id}")
                return updated_data
            else:
                logger.error(f"Failed to update user: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error in update_user: {e}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID"""
        try:
            data = self._read_json(self.users_file)
            
            if str(user_id) in data.get("users", {}):
                del data["users"][str(user_id)]
                
                # Update metadata
                data["metadata"]["last_updated"] = datetime.now().isoformat()
                data["metadata"]["total_users"] = len(data["users"])
                
                return self._write_json(self.users_file, data)
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def increment_user_stat(self, user_id: int, stat_name: str, amount: int = 1) -> bool:
        """Increment a user statistic"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        current = user.get(stat_name, 0)
        user[stat_name] = current + amount
        user["last_updated"] = datetime.now().isoformat()
        
        return self.update_user(user_id, user) is not None
    
    def get_top_users(self, limit: int = 10, by_field: str = "messages_count") -> List[Dict]:
        """Get top users by specified field"""
        users = self.get_all_users()
        
        # Sort by field (descending)
        sorted_users = sorted(
            users,
            key=lambda x: x.get(by_field, 0),
            reverse=True
        )
        
        return sorted_users[:limit]
    
    # ============ GROUP OPERATIONS ============
    
    def get_group(self, group_id: int) -> Optional[Dict]:
        """Get group data by ID"""
        data = self._read_json(self.groups_file)
        return data.get("groups", {}).get(str(group_id))
    
    def get_all_groups(self) -> List[Dict]:
        """Get all groups"""
        data = self._read_json(self.groups_file)
        return list(data.get("groups", {}).values())
    
    def update_group(self, group_id: int, group_data: Dict):
        """Update or create group data"""
        try:
            data = self._read_json(self.groups_file)
            
            if "groups" not in data:
                data["groups"] = {}
            
            # Get existing data or create new
            existing = data["groups"].get(str(group_id), {})
            
            # Merge with new data
            updated_data = {
                **existing,
                **group_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Ensure required fields
            if "id" not in updated_data:
                updated_data["id"] = group_id
            if "added_date" not in updated_data:
                updated_data["added_date"] = datetime.now().isoformat()
            
            data["groups"][str(group_id)] = updated_data
            
            # Update metadata
            data["metadata"] = {
                **data.get("metadata", {}),
                "last_updated": datetime.now().isoformat(),
                "total_groups": len(data["groups"])
            }
            
            success = self._write_json(self.groups_file, data)
            
            if success:
                logger.debug(f"Updated group: {group_id}")
                return updated_data
            else:
                logger.error(f"Failed to update group: {group_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error in update_group: {e}")
            return None
    
    def delete_group(self, group_id: int) -> bool:
        """Delete group by ID"""
        try:
            data = self._read_json(self.groups_file)
            
            if str(group_id) in data.get("groups", {}):
                del data["groups"][str(group_id)]
                
                # Update metadata
                data["metadata"]["last_updated"] = datetime.now().isoformat()
                data["metadata"]["total_groups"] = len(data["groups"])
                
                return self._write_json(self.groups_file, data)
            return False
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            return False
    
    def get_group_stat(self, group_id: int, stat_name: str, default: Any = 0) -> Any:
        """Get group statistic"""
        group = self.get_group(group_id)
        return group.get(stat_name, default) if group else default
    
    def increment_group_stat(self, group_id: int, stat_name: str, amount: int = 1) -> bool:
        """Increment a group statistic"""
        group = self.get_group(group_id)
        if not group:
            return False
        
        current = group.get(stat_name, 0)
        group[stat_name] = current + amount
        group["last_updated"] = datetime.now().isoformat()
        
        return self.update_group(group_id, group) is not None
    
    def get_top_groups(self, limit: int = 10, by_field: str = "member_count") -> List[Dict]:
        """Get top groups by specified field"""
        groups = self.get_all_groups()
        
        # Sort by field (descending)
        sorted_groups = sorted(
            groups,
            key=lambda x: x.get(by_field, 0),
            reverse=True
        )
        
        return sorted_groups[:limit]
    
    # ============ SYSTEM OPERATIONS ============
    
    def get_system_setting(self, key: str, default: Any = None) -> Any:
        """Get system setting"""
        data = self._read_json(self.system_file)
        return data.get("settings", {}).get(key, default)
    
    def set_system_setting(self, key: str, value: Any) -> bool:
        """Set system setting"""
        try:
            data = self._read_json(self.system_file)
            
            if "settings" not in data:
                data["settings"] = {}
            
            data["settings"][key] = value
            data["settings"]["last_updated"] = datetime.now().isoformat()
            
            return self._write_json(self.system_file, data)
        except Exception as e:
            logger.error(f"Error setting system setting {key}: {e}")
            return False
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        data = self._read_json(self.system_file)
        return data.get("stats", {})
    
    def update_system_stats(self, stats: Dict) -> bool:
        """Update system statistics"""
        try:
            data = self._read_json(self.system_file)
            
            if "stats" not in data:
                data["stats"] = {}
            
            data["stats"] = {**data["stats"], **stats}
            data["stats"]["last_updated"] = datetime.now().isoformat()
            
            return self._write_json(self.system_file, data)
        except Exception as e:
            logger.error(f"Error updating system stats: {e}")
            return False
    
    # ============ LOGGING OPERATIONS ============
    
    def log_action(self, action_type: str, user_id: int, details: Dict):
        """Log an action"""
        try:
            data = self._read_json(self.logs_file)
            
            if "actions" not in data:
                data["actions"] = []
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": action_type,
                "user_id": user_id,
                "details": details
            }
            
            data["actions"].append(log_entry)
            
            # Keep only last 1000 actions
            if len(data["actions"]) > 1000:
                data["actions"] = data["actions"][-1000:]
            
            return self._write_json(self.logs_file, data)
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    def log_error(self, error_type: str, error_message: str, traceback: str = ""):
        """Log an error"""
        try:
            data = self._read_json(self.logs_file)
            
            if "errors" not in data:
                data["errors"] = []
            
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": error_type,
                "message": error_message,
                "traceback": traceback
            }
            
            data["errors"].append(error_entry)
            
            # Keep only last 500 errors
            if len(data["errors"]) > 500:
                data["errors"] = data["errors"][-500:]
            
            return self._write_json(self.logs_file, data)
        except Exception as e:
            logger.error(f"Error logging error: {e}")
            return False
    
    def get_recent_actions(self, limit: int = 50) -> List[Dict]:
        """Get recent actions"""
        data = self._read_json(self.logs_file)
        actions = data.get("actions", [])
        return list(reversed(actions))[:limit]
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors"""
        data = self._read_json(self.logs_file)
        errors = data.get("errors", [])
        return list(reversed(errors))[:limit]
    
    # ============ BACKUP & MAINTENANCE ============
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create backup of all databases"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(Config.BASE_DIR, "backups", backup_name or f"backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            files_to_backup = [
                (self.users_file, "users.json"),
                (self.groups_file, "groups.json"),
                (self.system_file, "system.json"),
                (self.logs_file, "logs.json"),
                (Config.WG_JSON, "wg.json"),
                (Config.DEFAULT_JSON, "default.json")
            ]
            
            for source, filename in files_to_backup:
                if os.path.exists(source):
                    shutil.copy2(source, os.path.join(backup_dir, filename))
            
            # Create backup info file
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "total_users": len(self.get_all_users()),
                "total_groups": len(self.get_all_groups()),
                "files_backed_up": len(files_to_backup)
            }
            
            info_path = os.path.join(backup_dir, "backup_info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created backup at: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return ""
    
    def cleanup_old_backups(self, days_to_keep: int = 7):
        """Cleanup old backup files"""
        try:
            backups_dir = os.path.join(Config.BASE_DIR, "backups")
            if not os.path.exists(backups_dir):
                return
            
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 86400)
            
            for backup_folder in os.listdir(backups_dir):
                folder_path = os.path.join(backups_dir, backup_folder)
                if os.path.isdir(folder_path):
                    folder_time = os.path.getmtime(folder_path)
                    if folder_time < cutoff_time:
                        shutil.rmtree(folder_path)
                        logger.info(f"Removed old backup: {backup_folder}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        users = self.get_all_users()
        groups = self.get_all_groups()
        
        total_messages = sum(user.get('messages_count', 0) for user in users)
        total_reputation = sum(user.get('reputation', 0) for user in users)
        
        # User distribution by rank
        ranks = {}
        for user in users:
            rank = user.get('rank', 'Unknown')
            ranks[rank] = ranks.get(rank, 0) + 1
        
        # Activity by hour (simulated - would need time tracking)
        active_users_last_24h = len([
            u for u in users 
            if 'last_seen' in u and 
            (datetime.now() - datetime.fromisoformat(u['last_seen'])).days < 1
        ])
        
        return {
            "total_users": len(users),
            "total_groups": len(groups),
            "total_messages": total_messages,
            "total_reputation": total_reputation,
            "active_users_24h": active_users_last_24h,
            "rank_distribution": ranks,
            "database_size": self._get_database_size(),
            "last_backup": self.get_system_setting("last_backup", "Never"),
            "uptime": self.get_system_stats().get("uptime", "0:00:00")
        }
    
    def _get_database_size(self) -> str:
        """Calculate total database size"""
        total_size = 0
        files = [self.users_file, self.groups_file, self.system_file, self.logs_file]
        
        for file in files:
            if os.path.exists(file):
                total_size += os.path.getsize(file)
        
        # Convert to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024.0
        
        return f"{total_size:.2f} TB"
    
    def optimize_databases(self):
        """Optimize database files (remove old logs, compress, etc.)"""
        try:
            logger.info("Starting database optimization...")
            
            # 1. Cleanup old logs
            self._cleanup_old_logs()
            
            # 2. Remove inactive users (more than 90 days)
            self._remove_inactive_users()
            
            # 3. Compress JSON files (remove unnecessary whitespace)
            self._compress_json_files()
            
            # 4. Create fresh backup
            self.create_backup("pre_optimization")
            
            logger.info("Database optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing databases: {e}")
            return False
    
    def _cleanup_old_logs(self):
        """Cleanup logs older than 30 days"""
        data = self._read_json(self.logs_file)
        
        cutoff_date = datetime.now().isoformat()  # Simplified - should calculate 30 days ago
        
        # For production, implement actual date comparison
        # Keeping recent 500 entries for now
        if "actions" in data and len(data["actions"]) > 500:
            data["actions"] = data["actions"][-500:]
        
        if "errors" in data and len(data["errors"]) > 200:
            data["errors"] = data["errors"][-200:]
        
        self._write_json(self.logs_file, data)
    
    def _remove_inactive_users(self):
        """Remove users inactive for more than 90 days"""
        users_data = self._read_json(self.users_file)
        users = users_data.get("users", {})
        
        # For production, implement actual date checking
        # For now, just ensure database is not too large
        if len(users) > 10000:
            # Keep only top 5000 active users by message count
            sorted_users = sorted(
                users.items(),
                key=lambda x: x[1].get('messages_count', 0),
                reverse=True
            )[:5000]
            
            users_data["users"] = dict(sorted_users)
            self._write_json(self.users_file, users_data)
    
    def _compress_json_files(self):
        """Compress JSON files by removing extra whitespace"""
        files = [self.users_file, self.groups_file, self.system_file, self.logs_file]
        
        for file in files:
            if os.path.exists(file):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Write with minimal whitespace for production
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
                    
                    logger.debug(f"Compressed: {file}")
                except Exception as e:
                    logger.error(f"Error compressing {file}: {e}")