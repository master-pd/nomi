"""
Profile Engine - Handles user profile operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json

from core.utils.time_utils import format_duration, get_account_age
from core.utils.image_utils import download_profile_picture

class ProfileEngine:
    """Engine for user profile management"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_profile")
        self.json_loader = json_loader
        self.user_profiles = {}
        self.profile_cache = {}
        
    async def initialize(self):
        """Initialize profile engine"""
        self.logger.info("👤 Initializing profile engine...")
        await self._load_user_profiles()
        
    async def _load_user_profiles(self):
        """Load user profiles from storage"""
        try:
            profiles_file = Path("data/user_profiles.json")
            if profiles_file.exists():
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
                    
                self.logger.info(f"📂 Loaded {len(self.user_profiles)} user profiles")
        except Exception as e:
            self.logger.error(f"❌ Error loading user profiles: {e}")
            self.user_profiles = {}
            
    async def _save_user_profiles(self):
        """Save user profiles to storage"""
        try:
            profiles_file = Path("data/user_profiles.json")
            profiles_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving user profiles: {e}")
            
    async def get_user_profile(self, user_id: int, 
                             refresh: bool = False) -> Dict[str, Any]:
        """
        Get user profile
        
        Args:
            user_id: User ID
            refresh: Whether to refresh from source
            
        Returns:
            User profile data
        """
        # Check cache first
        if not refresh and user_id in self.profile_cache:
            cache_data = self.profile_cache[user_id]
            if datetime.now().timestamp() - cache_data.get("cached_at", 0) < 300:  # 5 minutes
                return cache_data.get("profile", {})
                
        # Get from stored profiles
        profile = self.user_profiles.get(str(user_id), {})
        
        # Update cache
        self.profile_cache[user_id] = {
            "profile": profile,
            "cached_at": datetime.now().timestamp()
        }
        
        return profile
        
    async def update_user_profile(self, user_id: int, 
                                user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            user_data: User data from Telegram
            
        Returns:
            Updated profile
        """
        user_id_str = str(user_id)
        
        # Get existing profile or create new
        profile = self.user_profiles.get(user_id_str, {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0,
            "join_count": 0,
            "reputation": 0,
            "badges": [],
            "rank": "member",
            "trust_score": 50
        })
        
        # Update basic info
        profile["first_name"] = user_data.get("first_name", "")
        profile["last_name"] = user_data.get("last_name", "")
        profile["username"] = user_data.get("username", "")
        profile["language_code"] = user_data.get("language_code", "bn")
        profile["is_bot"] = user_data.get("is_bot", False)
        profile["updated_at"] = datetime.now().isoformat()
        
        # Calculate account age
        account_age = await get_account_age(user_id)
        if account_age:
            profile["account_age_days"] = account_age.days
            profile["account_created"] = (datetime.now() - account_age).isoformat()
            
        # Download profile picture if available
        profile_photo = user_data.get("profile_photo")
        if profile_photo:
            photo_path = await download_profile_picture(profile_photo, user_id)
            if photo_path:
                profile["profile_picture"] = photo_path
                
        # Save profile
        self.user_profiles[user_id_str] = profile
        
        # Update cache
        self.profile_cache[user_id] = {
            "profile": profile,
            "cached_at": datetime.now().timestamp()
        }
        
        # Save to storage
        await self._save_user_profiles()
        
        self.logger.debug(f"📝 Updated profile for user {user_id}")
        return profile
        
    async def increment_message_count(self, user_id: int, 
                                    group_id: Optional[int] = None):
        """
        Increment user message count
        
        Args:
            user_id: User ID
            group_id: Group ID (optional)
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_profiles:
            await self.update_user_profile(user_id, {"id": user_id})
            
        profile = self.user_profiles[user_id_str]
        profile["message_count"] = profile.get("message_count", 0) + 1
        profile["last_message_at"] = datetime.now().isoformat()
        
        # Update group-specific stats
        if group_id:
            group_stats = profile.get("group_stats", {})
            group_id_str = str(group_id)
            
            if group_id_str not in group_stats:
                group_stats[group_id_str] = {
                    "message_count": 0,
                    "first_message": datetime.now().isoformat(),
                    "last_message": datetime.now().isoformat()
                }
                
            group_stats[group_id_str]["message_count"] += 1
            group_stats[group_id_str]["last_message"] = datetime.now().isoformat()
            profile["group_stats"] = group_stats
            
        # Update rank based on message count
        await self._update_user_rank(user_id_str, profile)
        
        # Save changes
        self.user_profiles[user_id_str] = profile
        await self._save_user_profiles()
        
    async def _update_user_rank(self, user_id_str: str, profile: Dict[str, Any]):
        """Update user rank based on activity"""
        message_count = profile.get("message_count", 0)
        reputation = profile.get("reputation", 0)
        
        # Determine rank
        if reputation >= 1000:
            rank = "elite"
        elif reputation >= 500:
            rank = "veteran"
        elif reputation >= 100:
            rank = "active"
        elif message_count >= 100:
            rank = "regular"
        elif message_count >= 10:
            rank = "member"
        else:
            rank = "new"
            
        profile["rank"] = rank
        
        # Update trust score
        trust_score = 50  # Base
        
        # Positive factors
        if message_count > 100:
            trust_score += 20
        if reputation > 0:
            trust_score += min(reputation // 10, 30)
        if profile.get("account_age_days", 0) > 30:
            trust_score += 10
            
        # Cap at 100
        profile["trust_score"] = min(100, max(0, trust_score))
        
    async def add_reputation(self, user_id: int, points: int, 
                           reason: str = "", given_by: Optional[int] = None):
        """
        Add reputation points to user
        
        Args:
            user_id: User ID
            points: Points to add (can be negative)
            reason: Reason for reputation change
            given_by: User who gave reputation
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_profiles:
            await self.update_user_profile(user_id, {"id": user_id})
            
        profile = self.user_profiles[user_id_str]
        current_reputation = profile.get("reputation", 0)
        new_reputation = current_reputation + points
        
        # Ensure reputation doesn't go below 0
        profile["reputation"] = max(0, new_reputation)
        
        # Record reputation history
        rep_history = profile.get("reputation_history", [])
        rep_history.append({
            "points": points,
            "reason": reason,
            "given_by": given_by,
            "timestamp": datetime.now().isoformat(),
            "total_after": profile["reputation"]
        })
        
        # Keep only last 50 records
        if len(rep_history) > 50:
            rep_history = rep_history[-50:]
            
        profile["reputation_history"] = rep_history
        
        # Update rank
        await self._update_user_rank(user_id_str, profile)
        
        # Save changes
        self.user_profiles[user_id_str] = profile
        await self._save_user_profiles()
        
        self.logger.info(f"⭐ User {user_id} reputation: {current_reputation} → {profile['reputation']} ({points} points)")
        
    async def add_badge(self, user_id: int, badge_name: str, 
                       badge_type: str = "achievement", 
                       description: str = ""):
        """
        Add badge to user
        
        Args:
            user_id: User ID
            badge_name: Name of badge
            badge_type: Type of badge
            description: Badge description
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_profiles:
            await self.update_user_profile(user_id, {"id": user_id})
            
        profile = self.user_profiles[user_id_str]
        badges = profile.get("badges", [])
        
        # Check if badge already exists
        if not any(b["name"] == badge_name for b in badges):
            new_badge = {
                "name": badge_name,
                "type": badge_type,
                "description": description,
                "earned_at": datetime.now().isoformat()
            }
            
            badges.append(new_badge)
            profile["badges"] = badges
            
            # Save changes
            self.user_profiles[user_id_str] = profile
            await self._save_user_profiles()
            
            self.logger.info(f"🎖️ Added badge '{badge_name}' to user {user_id}")
            
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            User statistics
        """
        profile = await self.get_user_profile(user_id)
        
        stats = {
            "user_id": user_id,
            "basic_info": {
                "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                "username": profile.get("username", ""),
                "account_age_days": profile.get("account_age_days", 0)
            },
            "activity": {
                "total_messages": profile.get("message_count", 0),
                "reputation": profile.get("reputation", 0),
                "rank": profile.get("rank", "new"),
                "trust_score": profile.get("trust_score", 50)
            },
            "achievements": {
                "badges_count": len(profile.get("badges", [])),
                "badges": profile.get("badges", [])
            },
            "timestamps": {
                "profile_created": profile.get("created_at"),
                "last_updated": profile.get("updated_at"),
                "last_message": profile.get("last_message_at")
            }
        }
        
        return stats
        
    async def get_top_users(self, criteria: str = "messages", 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users by criteria
        
        Args:
            criteria: Sorting criteria (messages, reputation, trust_score)
            limit: Number of users to return
            
        Returns:
            List of top users
        """
        users_list = []
        
        for user_id_str, profile in self.user_profiles.items():
            try:
                user_id = int(user_id_str)
                score = profile.get(criteria, 0)
                
                users_list.append({
                    "user_id": user_id,
                    "score": score,
                    "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                    "username": profile.get("username", ""),
                    "rank": profile.get("rank", "new")
                })
            except:
                continue
                
        # Sort by score
        users_list.sort(key=lambda x: x["score"], reverse=True)
        
        return users_list[:limit]
        
    async def generate_profile_card(self, user_id: int) -> Optional[str]:
        """
        Generate profile card image
        
        Args:
            user_id: User ID
            
        Returns:
            Path to profile card image or None
        """
        try:
            from core.utils.image_utils import create_profile_card
            
            # Get user profile
            profile = await self.get_user_profile(user_id)
            if not profile:
                return None
                
            # Prepare data for profile card
            profile_data = {
                "user_id": user_id,
                "first_name": profile.get("first_name", ""),
                "last_name": profile.get("last_name", ""),
                "username": profile.get("username", ""),
                "message_count": profile.get("message_count", 0),
                "reputation": profile.get("reputation", 0),
                "rank": profile.get("rank", "new"),
                "trust_score": profile.get("trust_score", 50),
                "badges": profile.get("badges", []),
                "profile_picture": profile.get("profile_picture")
            }
            
            # Create profile card
            card_path = await create_profile_card(profile_data)
            return card_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating profile card: {e}")
            return None
            
    async def cleanup_inactive_profiles(self, max_inactive_days: int = 90):
        """Cleanup profiles of inactive users"""
        current_time = datetime.now()
        inactive_users = []
        
        for user_id_str, profile in self.user_profiles.items():
            last_message = profile.get("last_message_at")
            if not last_message:
                # No activity recorded
                inactive_users.append(user_id_str)
                continue
                
            try:
                last_message_time = datetime.fromisoformat(last_message)
                inactive_days = (current_time - last_message_time).days
                
                if inactive_days > max_inactive_days:
                    inactive_users.append(user_id_str)
            except:
                inactive_users.append(user_id_str)
                
        # Remove inactive profiles (keep basic info)
        for user_id_str in inactive_users:
            if user_id_str in self.user_profiles:
                # Keep only essential info
                profile = self.user_profiles[user_id_str]
                minimal_profile = {
                    "user_id": profile.get("user_id"),
                    "first_name": profile.get("first_name", ""),
                    "last_name": profile.get("last_name", ""),
                    "username": profile.get("username", ""),
                    "created_at": profile.get("created_at"),
                    "inactive_since": datetime.now().isoformat()
                }
                
                self.user_profiles[user_id_str] = minimal_profile
                
        if inactive_users:
            await self._save_user_profiles()
            self.logger.info(f"🧹 Cleaned up {len(inactive_users)} inactive profiles")
            
    async def get_profile_stats(self) -> Dict[str, Any]:
        """Get profile engine statistics"""
        total_users = len(self.user_profiles)
        active_users = len([p for p in self.user_profiles.values() 
                          if p.get("message_count", 0) > 0])
                          
        # Calculate average stats
        total_messages = sum(p.get("message_count", 0) for p in self.user_profiles.values())
        total_reputation = sum(p.get("reputation", 0) for p in self.user_profiles.values())
        
        avg_messages = total_messages / total_users if total_users > 0 else 0
        avg_reputation = total_reputation / total_users if total_users > 0 else 0
        
        # Count badges
        total_badges = sum(len(p.get("badges", [])) for p in self.user_profiles.values())
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "total_messages": total_messages,
            "total_reputation": total_reputation,
            "total_badges": total_badges,
            "average_messages_per_user": round(avg_messages, 2),
            "average_reputation_per_user": round(avg_reputation, 2),
            "cache_size": len(self.profile_cache)
        }