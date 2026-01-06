"""
Group Engine - Handles group management and operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json

class GroupEngine:
    """Engine for group management"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_group")
        self.json_loader = json_loader
        self.groups = {}
        self.group_cache = {}
        
    async def initialize(self):
        """Initialize group engine"""
        self.logger.info("👥 Initializing group engine...")
        await self._load_groups()
        
    async def _load_groups(self):
        """Load groups from storage"""
        try:
            groups_file = Path("data/groups.json")
            if groups_file.exists():
                with open(groups_file, 'r', encoding='utf-8') as f:
                    self.groups = json.load(f)
                    
                self.logger.info(f"📂 Loaded {len(self.groups)} groups")
        except Exception as e:
            self.logger.error(f"❌ Error loading groups: {e}")
            self.groups = {}
            
    async def _save_groups(self):
        """Save groups to storage"""
        try:
            groups_file = Path("data/groups.json")
            groups_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(groups_file, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving groups: {e}")
            
    async def register_group(self, group_id: int, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new group
        
        Args:
            group_id: Group ID
            group_data: Group information
            
        Returns:
            Group registration data
        """
        group_id_str = str(group_id)
        
        if group_id_str in self.groups:
            # Update existing group
            group = self.groups[group_id_str]
            group["title"] = group_data.get("title", group.get("title", ""))
            group["member_count"] = group_data.get("member_count", group.get("member_count", 0))
            group["updated_at"] = datetime.now().isoformat()
        else:
            # Create new group
            group = {
                "group_id": group_id,
                "title": group_data.get("title", ""),
                "type": group_data.get("type", "group"),
                "member_count": group_data.get("member_count", 0),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "settings": {
                    "welcome_enabled": True,
                    "goodbye_enabled": True,
                    "auto_reply_enabled": True,
                    "moderation_enabled": True,
                    "voice_responses": False,
                    "image_welcome": True
                },
                "stats": {
                    "messages_today": 0,
                    "messages_total": 0,
                    "joins_today": 0,
                    "leaves_today": 0,
                    "warnings_today": 0
                },
                "rules": [],
                "admins": [],
                "blacklist": []
            }
            
        # Add group photo if available
        group_photo = group_data.get("photo")
        if group_photo:
            group["photo"] = group_photo
            
        # Save group
        self.groups[group_id_str] = group
        await self._save_groups()
        
        # Update cache
        self.group_cache[group_id] = {
            "group": group,
            "cached_at": datetime.now().timestamp()
        }
        
        self.logger.info(f"📝 Registered group: {group_data.get('title', group_id)}")
        return group
        
    async def get_group(self, group_id: int, 
                       refresh: bool = False) -> Dict[str, Any]:
        """
        Get group information
        
        Args:
            group_id: Group ID
            refresh: Whether to refresh from source
            
        Returns:
            Group data
        """
        # Check cache first
        if not refresh and group_id in self.group_cache:
            cache_data = self.group_cache[group_id]
            if datetime.now().timestamp() - cache_data.get("cached_at", 0) < 300:  # 5 minutes
                return cache_data.get("group", {})
                
        # Get from stored groups
        group = self.groups.get(str(group_id), {})
        
        # Update cache
        self.group_cache[group_id] = {
            "group": group,
            "cached_at": datetime.now().timestamp()
        }
        
        return group
        
    async def update_group_setting(self, group_id: int, setting: str, 
                                 value: Any) -> bool:
        """
        Update group setting
        
        Args:
            group_id: Group ID
            setting: Setting name
            value: New value
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        # Update setting
        if "." in setting:
            # Nested setting (e.g., "settings.welcome_enabled")
            keys = setting.split(".")
            current = group
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
        else:
            # Top-level setting
            group[setting] = value
            
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        # Update cache
        if group_id in self.group_cache:
            self.group_cache[group_id]["group"] = group
            self.group_cache[group_id]["cached_at"] = datetime.now().timestamp()
            
        self.logger.info(f"⚙️ Updated group {group_id} setting: {setting} = {value}")
        return True
        
    async def add_group_rule(self, group_id: int, rule: str, 
                           added_by: Optional[int] = None) -> bool:
        """
        Add rule to group
        
        Args:
            group_id: Group ID
            rule: Rule text
            added_by: User who added rule
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        # Initialize rules if not exists
        if "rules" not in group:
            group["rules"] = []
            
        # Add rule
        rule_data = {
            "text": rule,
            "added_by": added_by,
            "added_at": datetime.now().isoformat(),
            "rule_id": len(group["rules"]) + 1
        }
        
        group["rules"].append(rule_data)
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        self.logger.info(f"📜 Added rule to group {group_id}: {rule[:50]}...")
        return True
        
    async def remove_group_rule(self, group_id: int, rule_id: int) -> bool:
        """
        Remove rule from group
        
        Args:
            group_id: Group ID
            rule_id: Rule ID to remove
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        if "rules" not in group:
            return False
            
        # Find and remove rule
        new_rules = [r for r in group["rules"] if r.get("rule_id") != rule_id]
        
        if len(new_rules) == len(group["rules"]):
            return False  # Rule not found
            
        group["rules"] = new_rules
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        self.logger.info(f"🗑️ Removed rule {rule_id} from group {group_id}")
        return True
        
    async def increment_group_stat(self, group_id: int, stat_name: str, 
                                 amount: int = 1) -> bool:
        """
        Increment group statistic
        
        Args:
            group_id: Group ID
            stat_name: Statistic name
            amount: Amount to increment
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        # Initialize stats if not exists
        if "stats" not in group:
            group["stats"] = {}
            
        # Increment stat
        current_value = group["stats"].get(stat_name, 0)
        group["stats"][stat_name] = current_value + amount
        
        # Reset daily stats at midnight
        if stat_name.endswith("_today"):
            await self._check_daily_reset(group_id_str, group)
            
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        return True
        
    async def _check_daily_reset(self, group_id_str: str, group: Dict[str, Any]):
        """Check and reset daily statistics"""
        updated_at = group.get("updated_at")
        if not updated_at:
            return
            
        try:
            last_updated = datetime.fromisoformat(updated_at)
            now = datetime.now()
            
            # Reset if it's a new day
            if last_updated.date() < now.date():
                daily_stats = ["messages_today", "joins_today", 
                              "leaves_today", "warnings_today"]
                
                for stat in daily_stats:
                    if stat in group.get("stats", {}):
                        group["stats"][stat] = 0
                        
                self.logger.info(f"🔄 Reset daily stats for group {group_id_str}")
        except:
            pass
            
    async def add_group_admin(self, group_id: int, user_id: int, 
                            added_by: Optional[int] = None) -> bool:
        """
        Add admin to group
        
        Args:
            group_id: Group ID
            user_id: User ID to add as admin
            added_by: User who added admin
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        # Initialize admins if not exists
        if "admins" not in group:
            group["admins"] = []
            
        # Check if already admin
        if user_id in group["admins"]:
            return False
            
        # Add admin
        group["admins"].append(user_id)
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        self.logger.info(f"👑 Added admin {user_id} to group {group_id}")
        return True
        
    async def remove_group_admin(self, group_id: int, user_id: int) -> bool:
        """
        Remove admin from group
        
        Args:
            group_id: Group ID
            user_id: User ID to remove as admin
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        if "admins" not in group:
            return False
            
        # Remove admin
        if user_id in group["admins"]:
            group["admins"].remove(user_id)
            group["updated_at"] = datetime.now().isoformat()
            
            # Save changes
            self.groups[group_id_str] = group
            await self._save_groups()
            
            self.logger.info(f"👑 Removed admin {user_id} from group {group_id}")
            return True
            
        return False
        
    async def is_group_admin(self, group_id: int, user_id: int) -> bool:
        """
        Check if user is group admin
        
        Args:
            group_id: Group ID
            user_id: User ID
            
        Returns:
            True if user is admin
        """
        group = await self.get_group(group_id)
        
        if not group:
            return False
            
        return user_id in group.get("admins", [])
        
    async def add_to_blacklist(self, group_id: int, user_id: int, 
                             reason: str = "", banned_by: Optional[int] = None) -> bool:
        """
        Add user to group blacklist
        
        Args:
            group_id: Group ID
            user_id: User ID to blacklist
            reason: Ban reason
            banned_by: User who banned
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        # Initialize blacklist if not exists
        if "blacklist" not in group:
            group["blacklist"] = []
            
        # Check if already blacklisted
        blacklist_entry = next((b for b in group["blacklist"] 
                              if b.get("user_id") == user_id), None)
                              
        if blacklist_entry:
            # Update existing entry
            blacklist_entry["reason"] = reason
            blacklist_entry["banned_by"] = banned_by
            blacklist_entry["banned_at"] = datetime.now().isoformat()
        else:
            # Add new entry
            blacklist_entry = {
                "user_id": user_id,
                "reason": reason,
                "banned_by": banned_by,
                "banned_at": datetime.now().isoformat()
            }
            group["blacklist"].append(blacklist_entry)
            
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        self.logger.warning(f"🚫 Added {user_id} to blacklist in group {group_id}")
        return True
        
    async def remove_from_blacklist(self, group_id: int, user_id: int) -> bool:
        """
        Remove user from group blacklist
        
        Args:
            group_id: Group ID
            user_id: User ID to unblacklist
            
        Returns:
            True if successful
        """
        group_id_str = str(group_id)
        
        if group_id_str not in self.groups:
            return False
            
        group = self.groups[group_id_str]
        
        if "blacklist" not in group:
            return False
            
        # Remove from blacklist
        new_blacklist = [b for b in group["blacklist"] 
                        if b.get("user_id") != user_id]
                        
        if len(new_blacklist) == len(group["blacklist"]):
            return False  # User not in blacklist
            
        group["blacklist"] = new_blacklist
        group["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        self.groups[group_id_str] = group
        await self._save_groups()
        
        self.logger.info(f"✅ Removed {user_id} from blacklist in group {group_id}")
        return True
        
    async def is_blacklisted(self, group_id: int, user_id: int) -> bool:
        """
        Check if user is blacklisted in group
        
        Args:
            group_id: Group ID
            user_id: User ID
            
        Returns:
            True if user is blacklisted
        """
        group = await self.get_group(group_id)
        
        if not group or "blacklist" not in group:
            return False
            
        return any(b.get("user_id") == user_id for b in group["blacklist"])
        
    async def get_group_stats(self, group_id: int) -> Dict[str, Any]:
        """
        Get comprehensive group statistics
        
        Args:
            group_id: Group ID
            
        Returns:
            Group statistics
        """
        group = await self.get_group(group_id)
        
        if not group:
            return {}
            
        stats = {
            "group_id": group_id,
            "basic_info": {
                "title": group.get("title", ""),
                "type": group.get("type", "group"),
                "member_count": group.get("member_count", 0),
                "created_at": group.get("created_at"),
                "updated_at": group.get("updated_at")
            },
            "activity": group.get("stats", {}),
            "settings": group.get("settings", {}),
            "administration": {
                "admins_count": len(group.get("admins", [])),
                "blacklist_count": len(group.get("blacklist", [])),
                "rules_count": len(group.get("rules", []))
            },
            "features": {
                "welcome_enabled": group.get("settings", {}).get("welcome_enabled", True),
                "goodbye_enabled": group.get("settings", {}).get("goodbye_enabled", True),
                "moderation_enabled": group.get("settings", {}).get("moderation_enabled", True)
            }
        }
        
        return stats
        
    async def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get list of all groups"""
        groups_list = []
        
        for group_id_str, group in self.groups.items():
            try:
                groups_list.append({
                    "group_id": int(group_id_str),
                    "title": group.get("title", ""),
                    "member_count": group.get("member_count", 0),
                    "created_at": group.get("created_at"),
                    "updated_at": group.get("updated_at"),
                    "settings": group.get("settings", {})
                })
            except:
                continue
                
        return groups_list
        
    async def cleanup_inactive_groups(self, max_inactive_days: int = 30):
        """Cleanup inactive groups"""
        current_time = datetime.now()
        inactive_groups = []
        
        for group_id_str, group in self.groups.items():
            updated_at = group.get("updated_at")
            if not updated_at:
                inactive_groups.append(group_id_str)
                continue
                
            try:
                updated_time = datetime.fromisoformat(updated_at)
                inactive_days = (current_time - updated_time).days
                
                if inactive_days > max_inactive_days:
                    inactive_groups.append(group_id_str)
            except:
                inactive_groups.append(group_id_str)
                
        # Remove inactive groups
        for group_id_str in inactive_groups:
            if group_id_str in self.groups:
                del self.groups[group_id_str]
                
                # Remove from cache
                group_id = int(group_id_str)
                if group_id in self.group_cache:
                    del self.group_cache[group_id]
                    
        if inactive_groups:
            await self._save_groups()
            self.logger.info(f"🧹 Cleaned up {len(inactive_groups)} inactive groups")
            
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get group engine statistics"""
        total_groups = len(self.groups)
        
        # Count groups by type
        types_count = {}
        for group in self.groups.values():
            gtype = group.get("type", "group")
            types_count[gtype] = types_count.get(gtype, 0) + 1
            
        # Calculate average member count
        total_members = sum(g.get("member_count", 0) for g in self.groups.values())
        avg_members = total_members / total_groups if total_groups > 0 else 0
        
        # Count active groups (updated in last 7 days)
        active_groups = 0
        for group in self.groups.values():
            updated_at = group.get("updated_at")
            if updated_at:
                try:
                    updated_time = datetime.fromisoformat(updated_at)
                    if (datetime.now() - updated_time).days < 7:
                        active_groups += 1
                except:
                    pass
                    
        return {
            "total_groups": total_groups,
            "active_groups": active_groups,
            "inactive_groups": total_groups - active_groups,
            "total_members": total_members,
            "average_members_per_group": round(avg_members, 2),
            "groups_by_type": types_count,
            "cache_size": len(self.group_cache)
        }