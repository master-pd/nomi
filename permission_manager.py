"""
Permission Manager - Manages user and group permissions
"""

import logging
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import asyncio

class PermissionLevel(Enum):
    """Permission levels"""
    BANNED = 0
    USER = 1
    TRUSTED = 2
    MODERATOR = 3
    ADMIN = 4
    SUPER_ADMIN = 5
    OWNER = 6

@dataclass
class UserPermission:
    """User permission data"""
    user_id: int
    permission_level: PermissionLevel
    granted_by: Optional[int] = None
    granted_at: float = 0.0
    expires_at: Optional[float] = None
    reason: str = ""

@dataclass
class GroupPermission:
    """Group permission data"""
    group_id: int
    enabled_features: Set[str]
    disabled_features: Set[str]
    restrictions: Dict[str, Any]

class PermissionManager:
    """Manages permissions system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_permission")
        self.user_permissions: Dict[int, UserPermission] = {}
        self.group_permissions: Dict[int, GroupPermission] = {}
        self.default_permissions = {
            PermissionLevel.USER: {
                "can_send_messages": True,
                "can_use_basic_commands": True,
                "can_view_stats": True
            },
            PermissionLevel.TRUSTED: {
                "can_send_messages": True,
                "can_use_basic_commands": True,
                "can_view_stats": True,
                "can_use_advanced_commands": True,
                "can_view_admin_stats": False
            },
            PermissionLevel.MODERATOR: {
                "can_send_messages": True,
                "can_use_all_commands": True,
                "can_moderate": True,
                "can_warn_users": True,
                "can_mute_users": True,
                "can_view_admin_stats": True
            },
            PermissionLevel.ADMIN: {
                "can_send_messages": True,
                "can_use_all_commands": True,
                "can_moderate": True,
                "can_manage_group": True,
                "can_change_settings": True,
                "can_promote_demote": True,
                "can_view_admin_stats": True
            }
        }
        
    async def initialize(self):
        """Initialize permission manager"""
        self.logger.info("🔐 Initializing permission manager...")
        # Load saved permissions from database
        await self._load_permissions()
        
    async def _load_permissions(self):
        """Load permissions from storage"""
        # TODO: Load from database
        pass
        
    async def _save_permissions(self):
        """Save permissions to storage"""
        # TODO: Save to database
        pass
        
    def get_user_permission(self, user_id: int) -> PermissionLevel:
        """
        Get user's permission level
        
        Args:
            user_id: User ID
            
        Returns:
            Permission level
        """
        if user_id in self.user_permissions:
            perm = self.user_permissions[user_id]
            # Check if expired
            if perm.expires_at and perm.expires_at < asyncio.get_event_loop().time():
                # Permission expired, revert to USER
                del self.user_permissions[user_id]
                return PermissionLevel.USER
            return perm.permission_level
            
        return PermissionLevel.USER
        
    def set_user_permission(self, user_id: int, level: PermissionLevel, 
                           granted_by: Optional[int] = None, duration: Optional[int] = None,
                           reason: str = ""):
        """
        Set user permission level
        
        Args:
            user_id: User ID
            level: Permission level
            granted_by: Who granted this permission
            duration: Duration in seconds (None for permanent)
            reason: Reason for permission change
        """
        expires_at = None
        if duration:
            expires_at = asyncio.get_event_loop().time() + duration
            
        permission = UserPermission(
            user_id=user_id,
            permission_level=level,
            granted_by=granted_by,
            granted_at=asyncio.get_event_loop().time(),
            expires_at=expires_at,
            reason=reason
        )
        
        self.user_permissions[user_id] = permission
        self.logger.info(f"📝 Set permission for user {user_id}: {level.name}")
        
        # Save changes
        asyncio.create_task(self._save_permissions())
        
    def check_permission(self, user_id: int, required_level: PermissionLevel) -> bool:
        """
        Check if user has required permission level
        
        Args:
            user_id: User ID
            required_level: Required permission level
            
        Returns:
            True if user has permission
        """
        user_level = self.get_user_permission(user_id)
        return user_level.value >= required_level.value
        
    def can_perform_action(self, user_id: int, action: str) -> bool:
        """
        Check if user can perform specific action
        
        Args:
            user_id: User ID
            action: Action to check
            
        Returns:
            True if allowed
        """
        user_level = self.get_user_permission(user_id)
        
        if user_level in self.default_permissions:
            permissions = self.default_permissions[user_level]
            return permissions.get(action, False)
            
        return False
        
    def get_group_permission(self, group_id: int) -> GroupPermission:
        """
        Get group permissions
        
        Args:
            group_id: Group ID
            
        Returns:
            Group permission object
        """
        if group_id in self.group_permissions:
            return self.group_permissions[group_id]
            
        # Return default
        return GroupPermission(
            group_id=group_id,
            enabled_features=set(["welcome", "goodbye", "auto_reply"]),
            disabled_features=set(),
            restrictions={}
        )
        
    def set_group_permission(self, group_id: int, enabled: List[str] = None, 
                            disabled: List[str] = None, restrictions: Dict = None):
        """
        Set group permissions
        
        Args:
            group_id: Group ID
            enabled: List of enabled features
            disabled: List of disabled features
            restrictions: Additional restrictions
        """
        if group_id not in self.group_permissions:
            self.group_permissions[group_id] = GroupPermission(
                group_id=group_id,
                enabled_features=set(),
                disabled_features=set(),
                restrictions={}
            )
            
        group_perm = self.group_permissions[group_id]
        
        if enabled:
            group_perm.enabled_features.update(enabled)
            
        if disabled:
            group_perm.disabled_features.update(disabled)
            
        if restrictions:
            group_perm.restrictions.update(restrictions)
            
        self.logger.info(f"📝 Updated permissions for group {group_id}")
        
    def is_feature_enabled(self, group_id: int, feature: str) -> bool:
        """
        Check if feature is enabled in group
        
        Args:
            group_id: Group ID
            feature: Feature name
            
        Returns:
            True if enabled
        """
        group_perm = self.get_group_permission(group_id)
        
        if feature in group_perm.disabled_features:
            return False
            
        if feature in group_perm.enabled_features:
            return True
            
        # Default enabled features
        default_enabled = {"welcome", "goodbye", "auto_reply"}
        return feature in default_enabled
        
    def ban_user(self, user_id: int, reason: str = "", duration: Optional[int] = None):
        """Ban a user"""
        self.set_user_permission(
            user_id=user_id,
            level=PermissionLevel.BANNED,
            reason=reason,
            duration=duration
        )
        
    def unban_user(self, user_id: int):
        """Unban a user"""
        if user_id in self.user_permissions:
            # Check if banned
            if self.user_permissions[user_id].permission_level == PermissionLevel.BANNED:
                del self.user_permissions[user_id]
                self.logger.info(f"✅ Unbanned user {user_id}")
                
    def promote_user(self, user_id: int, to_level: PermissionLevel, 
                    promoted_by: Optional[int] = None, reason: str = ""):
        """Promote a user"""
        current_level = self.get_user_permission(user_id)
        
        if to_level.value > current_level.value:
            self.set_user_permission(
                user_id=user_id,
                level=to_level,
                granted_by=promoted_by,
                reason=reason
            )
            
    def demote_user(self, user_id: int, to_level: PermissionLevel,
                   demoted_by: Optional[int] = None, reason: str = ""):
        """Demote a user"""
        current_level = self.get_user_permission(user_id)
        
        if to_level.value < current_level.value:
            self.set_user_permission(
                user_id=user_id,
                level=to_level,
                granted_by=demoted_by,
                reason=reason
            )
            
    def get_permission_info(self, user_id: int) -> Dict[str, Any]:
        """Get detailed permission info for user"""
        if user_id in self.user_permissions:
            perm = self.user_permissions[user_id]
            return {
                "user_id": user_id,
                "level": perm.permission_level.name,
                "level_value": perm.permission_level.value,
                "granted_by": perm.granted_by,
                "granted_at": perm.granted_at,
                "expires_at": perm.expires_at,
                "reason": perm.reason,
                "is_expired": perm.expires_at and perm.expires_at < asyncio.get_event_loop().time()
            }
        else:
            return {
                "user_id": user_id,
                "level": PermissionLevel.USER.name,
                "level_value": PermissionLevel.USER.value,
                "is_default": True
            }
            
    def cleanup_expired(self):
        """Cleanup expired permissions"""
        current_time = asyncio.get_event_loop().time()
        expired = []
        
        for user_id, perm in self.user_permissions.items():
            if perm.expires_at and perm.expires_at < current_time:
                expired.append(user_id)
                
        for user_id in expired:
            del self.user_permissions[user_id]
            
        if expired:
            self.logger.info(f"🧹 Cleaned up {len(expired)} expired permissions")