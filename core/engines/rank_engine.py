"""
Rank Engine - Handles user ranking and leveling system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math

class RankEngine:
    """Engine for user ranking and leveling"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_rank")
        self.json_loader = json_loader
        self.rank_config = {}
        self.user_ranks = {}
        
    async def initialize(self):
        """Initialize rank engine"""
        self.logger.info("🏆 Initializing rank engine...")
        await self._load_rank_config()
        
    async def _load_rank_config(self):
        """Load rank configuration"""
        try:
            config = await self.json_loader.load("config/ranks.json")
            self.rank_config = config.get("ranks", {})
            
            if not self.rank_config:
                # Default rank configuration
                self.rank_config = {
                    "levels": {
                        1: {"name": "নতুন", "min_xp": 0, "color": "#95a5a6"},
                        2: {"name": "সদস্য", "min_xp": 100, "color": "#3498db"},
                        3: {"name": "নিয়মিত", "min_xp": 500, "color": "#2ecc71"},
                        4: {"name": "সক্রিয়", "min_xp": 1000, "color": "#9b59b6"},
                        5: {"name": "অভিজ্ঞ", "min_xp": 2500, "color": "#e67e22"},
                        6: {"name": "বিশেষজ্ঞ", "min_xp": 5000, "color": "#e74c3c"},
                        7: {"name": "মাস্টার", "min_xp": 10000, "color": "#f1c40f"},
                        8: {"name": "গ্র্যান্ড মাস্টার", "min_xp": 20000, "color": "#1abc9c"},
                        9: {"name": "লেজেন্ড", "min_xp": 50000, "color": "#9b59b6"},
                        10: {"name": "মিথিক্যাল", "min_xp": 100000, "color": "#e74c3c"}
                    },
                    "xp_gain": {
                        "message": 10,
                        "voice_message": 15,
                        "photo_message": 12,
                        "command_usage": 5,
                        "daily_login": 50,
                        "help_other": 20,
                        "report_issue": 25,
                        "suggest_feature": 30
                    },
                    "rank_badges": {
                        "new": "🆕",
                        "member": "👤",
                        "regular": "⭐",
                        "active": "🔥",
                        "experienced": "🎯",
                        "expert": "🧠",
                        "master": "👑",
                        "grand_master": "⚡",
                        "legend": "🌈",
                        "mythical": "✨"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error loading rank config: {e}")
            await self._create_default_config()
            
    async def _create_default_config(self):
        """Create default rank configuration"""
        self.rank_config = {
            "levels": {
                1: {"name": "নতুন", "min_xp": 0, "color": "#95a5a6"},
                2: {"name": "সদস্য", "min_xp": 100, "color": "#3498db"},
                3: {"name": "নিয়মিত", "min_xp": 500, "color": "#2ecc71"},
                4: {"name": "সক্রিয়", "min_xp": 1000, "color": "#9b59b6"},
                5: {"name": "অভিজ্ঞ", "min_xp": 2500, "color": "#e67e22"},
                6: {"name": "বিশেষজ্ঞ", "min_xp": 5000, "color": "#e74c3c"},
                7: {"name": "মাস্টার", "min_xp": 10000, "color": "#f1c40f"},
                8: {"name": "গ্র্যান্ড মাস্টার", "min_xp": 20000, "color": "#1abc9c"},
                9: {"name": "লেজেন্ড", "min_xp": 50000, "color": "#9b59b6"},
                        10: {"name": "মিথিক্যাল", "min_xp": 100000, "color": "#e74c3c"}
                    }
                }
                
        # Save default config
        await self.json_loader.save("config/ranks.json", {"ranks": self.rank_config})
        
    async def get_user_rank(self, user_id: int) -> Dict[str, Any]:
        """
        Get user rank information
        
        Args:
            user_id: User ID
            
        Returns:
            Rank information
        """
        if user_id in self.user_ranks:
            return self.user_ranks[user_id]
            
        # Load from storage or create new
        user_rank = await self._load_user_rank(user_id)
        if not user_rank:
            user_rank = await self._create_new_user_rank(user_id)
            
        self.user_ranks[user_id] = user_rank
        return user_rank
        
    async def _load_user_rank(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load user rank from storage"""
        # This would load from database or file
        # For now, return None to create new
        return None
        
    async def _create_new_user_rank(self, user_id: int) -> Dict[str, Any]:
        """Create new user rank entry"""
        return {
            "user_id": user_id,
            "xp": 0,
            "level": 1,
            "rank_name": self.rank_config["levels"][1]["name"],
            "messages_sent": 0,
            "commands_used": 0,
            "days_active": 1,
            "streak_days": 1,
            "last_active": datetime.now().isoformat(),
            "achievements": [],
            "rank_history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
    async def add_xp(self, user_id: int, xp_type: str, amount: Optional[int] = None,
                   reason: str = "") -> Dict[str, Any]:
        """
        Add XP to user
        
        Args:
            user_id: User ID
            xp_type: Type of XP gain
            amount: XP amount (None to use default from config)
            reason: Reason for XP gain
            
        Returns:
            Updated rank information
        """
        # Get user rank
        user_rank = await self.get_user_rank(user_id)
        
        # Determine XP amount
        if amount is None:
            amount = self.rank_config.get("xp_gain", {}).get(xp_type, 10)
            
        # Add XP
        old_xp = user_rank["xp"]
        old_level = user_rank["level"]
        
        user_rank["xp"] += amount
        user_rank["updated_at"] = datetime.now().isoformat()
        
        # Update statistics based on XP type
        if xp_type == "message":
            user_rank["messages_sent"] += 1
        elif xp_type == "command_usage":
            user_rank["commands_used"] += 1
            
        # Check for level up
        new_level = await self._calculate_level(user_rank["xp"])
        
        if new_level > old_level:
            user_rank["level"] = new_level
            user_rank["rank_name"] = self.rank_config["levels"][new_level]["name"]
            
            # Record level up
            level_up_record = {
                "old_level": old_level,
                "new_level": new_level,
                "timestamp": datetime.now().isoformat(),
                "total_xp": user_rank["xp"],
                "reason": reason
            }
            
            user_rank["rank_history"].append(level_up_record)
            
            # Keep only last 20 level ups
            if len(user_rank["rank_history"]) > 20:
                user_rank["rank_history"] = user_rank["rank_history"][-20:]
                
            self.logger.info(f"🎉 User {user_id} leveled up: {old_level} → {new_level}")
            
        # Save updated rank
        self.user_ranks[user_id] = user_rank
        await self._save_user_rank(user_id, user_rank)
        
        return {
            "user_id": user_id,
            "old_xp": old_xp,
            "new_xp": user_rank["xp"],
            "old_level": old_level,
            "new_level": user_rank["level"],
            "xp_gained": amount,
            "leveled_up": new_level > old_level,
            "next_level_xp": await self._get_next_level_xp(user_rank["xp"]),
            "progress_percentage": await self._calculate_progress_percentage(user_rank["xp"])
        }
        
    async def _calculate_level(self, xp: int) -> int:
        """
        Calculate level based on XP
        
        Args:
            xp: Total XP
            
        Returns:
            Level number
        """
        levels = self.rank_config.get("levels", {})
        
        # Find highest level where XP >= min_xp
        max_level = 1
        for level_num, level_data in levels.items():
            if xp >= level_data.get("min_xp", 0):
                max_level = max(max_level, level_num)
                
        return max_level
        
    async def _get_next_level_xp(self, current_xp: int) -> int:
        """
        Get XP required for next level
        
        Args:
            current_xp: Current XP
            
        Returns:
            XP needed for next level
        """
        current_level = await self._calculate_level(current_xp)
        levels = self.rank_config.get("levels", {})
        
        next_level = current_level + 1
        if next_level in levels:
            return levels[next_level]["min_xp"] - current_xp
        else:
            # Max level reached
            return 0
            
    async def _calculate_progress_percentage(self, xp: int) -> float:
        """
        Calculate progress percentage to next level
        
        Args:
            xp: Current XP
            
        Returns:
            Progress percentage (0-100)
        """
        current_level = await self._calculate_level(xp)
        levels = self.rank_config.get("levels", {})
        
        if current_level >= max(levels.keys(), default=current_level):
            return 100.0
            
        current_level_data = levels[current_level]
        next_level_data = levels[current_level + 1]
        
        current_min_xp = current_level_data["min_xp"]
        next_min_xp = next_level_data["min_xp"]
        
        progress_in_level = xp - current_min_xp
        level_range = next_min_xp - current_min_xp
        
        return (progress_in_level / level_range) * 100 if level_range > 0 else 0
        
    async def _save_user_rank(self, user_id: int, user_rank: Dict[str, Any]):
        """Save user rank to storage"""
        # This would save to database or file
        # For now, just update in-memory cache
        pass
        
    async def get_rank_card(self, user_id: int) -> Dict[str, Any]:
        """
        Generate rank card information
        
        Args:
            user_id: User ID
            
        Returns:
            Rank card data
        """
        user_rank = await self.get_user_rank(user_id)
        
        current_level = user_rank["level"]
        current_xp = user_rank["xp"]
        
        # Get level information
        level_info = self.rank_config["levels"].get(current_level, {})
        next_level_info = self.rank_config["levels"].get(current_level + 1, {})
        
        # Calculate progress
        next_level_xp = await self._get_next_level_xp(current_xp)
        progress_percentage = await self._calculate_progress_percentage(current_xp)
        
        # Get rank badge
        rank_badges = self.rank_config.get("rank_badges", {})
        rank_name_lower = user_rank["rank_name"].lower()
        badge = rank_badges.get(rank_name_lower, "⭐")
        
        return {
            "user_id": user_id,
            "rank": user_rank["rank_name"],
            "level": current_level,
            "xp": current_xp,
            "badge": badge,
            "color": level_info.get("color", "#3498db"),
            "next_level_xp": next_level_xp,
            "progress_percentage": round(progress_percentage, 1),
            "messages_sent": user_rank["messages_sent"],
            "commands_used": user_rank["commands_used"],
            "days_active": user_rank["days_active"],
            "streak_days": user_rank["streak_days"],
            "achievements_count": len(user_rank.get("achievements", [])),
            "rank_position": await self.get_global_rank_position(user_id)
        }
        
    async def get_global_rank_position(self, user_id: int) -> int:
        """
        Get user's global rank position
        
        Args:
            user_id: User ID
            
        Returns:
            Rank position (1-based)
        """
        # This would query all users sorted by XP
        # For now, return placeholder
        return 1
        
    async def get_top_users(self, limit: int = 10, criteria: str = "xp") -> List[Dict[str, Any]]:
        """
        Get top users by criteria
        
        Args:
            limit: Number of users to return
            criteria: Sorting criteria (xp, level, messages_sent)
            
        Returns:
            List of top users
        """
        # This would query database
        # For now, return dummy data
        top_users = []
        
        for i in range(min(limit, 10)):
            top_users.append({
                "position": i + 1,
                "user_id": 1000 + i,
                "username": f"user_{i}",
                "rank": f"Rank {i+1}",
                "level": 10 - i,
                "xp": 10000 - (i * 1000),
                "badge": "⭐"
            })
            
        return top_users
        
    async def add_achievement(self, user_id: int, achievement_id: str, 
                            achievement_name: str, description: str = ""):
        """
        Add achievement to user
        
        Args:
            user_id: User ID
            achievement_id: Achievement ID
            achievement_name: Achievement name
            description: Achievement description
        """
        user_rank = await self.get_user_rank(user_id)
        
        achievements = user_rank.get("achievements", [])
        
        # Check if achievement already exists
        if not any(a["id"] == achievement_id for a in achievements):
            achievement = {
                "id": achievement_id,
                "name": achievement_name,
                "description": description,
                "earned_at": datetime.now().isoformat()
            }
            
            achievements.append(achievement)
            user_rank["achievements"] = achievements
            
            # Add XP for achievement
            await self.add_xp(user_id, "achievement", 100, f"Achievement: {achievement_name}")
            
            self.logger.info(f"🏆 User {user_id} earned achievement: {achievement_name}")
            
    async def update_daily_streak(self, user_id: int) -> Dict[str, Any]:
        """
        Update user's daily streak
        
        Args:
            user_id: User ID
            
        Returns:
            Streak update information
        """
        user_rank = await self.get_user_rank(user_id)
        
        today = datetime.now().date()
        last_active = datetime.fromisoformat(user_rank["last_active"]).date()
        
        if last_active == today:
            # Already active today
            return {
                "streak_updated": False,
                "current_streak": user_rank["streak_days"],
                "message": "Already active today"
            }
            
        days_diff = (today - last_active).days
        
        if days_diff == 1:
            # Consecutive day
            user_rank["streak_days"] += 1
            streak_bonus = min(user_rank["streak_days"] * 5, 50)  # Max 50 XP bonus
        elif days_diff > 1:
            # Broken streak
            user_rank["streak_days"] = 1
            streak_bonus = 0
        else:
            # Same day (shouldn't happen)
            user_rank["streak_days"] = user_rank["streak_days"]
            streak_bonus = 0
            
        # Update last active
        user_rank["last_active"] = datetime.now().isoformat()
        user_rank["days_active"] += 1
        
        # Add XP for daily login
        login_xp = self.rank_config.get("xp_gain", {}).get("daily_login", 50)
        total_xp = login_xp + streak_bonus
        
        await self.add_xp(user_id, "daily_login", total_xp, "Daily login bonus")
        
        return {
            "streak_updated": True,
            "current_streak": user_rank["streak_days"],
            "days_active": user_rank["days_active"],
            "xp_gained": total_xp,
            "streak_bonus": streak_bonus,
            "streak_broken": days_diff > 1
        }
        
    async def calculate_leaderboard(self, group_id: Optional[int] = None, 
                                  time_frame: str = "all_time") -> List[Dict[str, Any]]:
        """
        Calculate leaderboard
        
        Args:
            group_id: Group ID (None for global)
            time_frame: Time frame (daily, weekly, monthly, all_time)
            
        Returns:
            Leaderboard data
        """
        # This would calculate based on actual data
        # For now, return dummy leaderboard
        
        leaderboard = []
        
        for i in range(10):
            leaderboard.append({
                "rank": i + 1,
                "user_id": 1000 + i,
                "username": f"top_user_{i}",
                "xp": 10000 - (i * 800),
                "level": 10 - i,
                "messages": 500 - (i * 40),
                "progress": 100 - (i * 8)
            })
            
        return leaderboard
        
    async def get_user_rank_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's rank history
        
        Args:
            user_id: User ID
            limit: Maximum number of history entries
            
        Returns:
            Rank history
        """
        user_rank = await self.get_user_rank(user_id)
        history = user_rank.get("rank_history", [])
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return history[:limit]
        
    async def reset_user_rank(self, user_id: int, reason: str = "") -> bool:
        """
        Reset user's rank (admin function)
        
        Args:
            user_id: User ID
            reason: Reset reason
            
        Returns:
            True if successful
        """
        if user_id in self.user_ranks:
            del self.user_ranks[user_id]
            
        # Create new rank
        await self._create_new_user_rank(user_id)
        
        self.logger.warning(f"🔄 Reset rank for user {user_id}: {reason}")
        return True
        
    async def get_rank_system_stats(self) -> Dict[str, Any]:
        """Get rank system statistics"""
        total_users = len(self.user_ranks)
        
        if total_users == 0:
            return {
                "total_users": 0,
                "average_level": 0,
                "average_xp": 0,
                "top_rank": "নতুন",
                "level_distribution": {}
            }
            
        # Calculate averages
        total_xp = sum(r["xp"] for r in self.user_ranks.values())
        total_level = sum(r["level"] for r in self.user_ranks.values())
        
        # Calculate level distribution
        level_dist = {}
        for rank in self.user_ranks.values():
            level = rank["level"]
            level_dist[level] = level_dist.get(level, 0) + 1
            
        # Find most common rank
        rank_names = [r["rank_name"] for r in self.user_ranks.values()]
        most_common_rank = max(set(rank_names), key=rank_names.count, default="নতুন")
        
        return {
            "total_users": total_users,
            "average_level": round(total_level / total_users, 2),
            "average_xp": round(total_xp / total_users, 2),
            "top_rank": most_common_rank,
            "level_distribution": level_dist,
            "max_level_reached": max([r["level"] for r in self.user_ranks.values()], default=1),
            "total_xp_in_system": total_xp
        }
        
    async def export_rank_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export rank data
        
        Args:
            format: Export format
            
        Returns:
            Exported data
        """
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_users": len(self.user_ranks),
            "rank_config": self.rank_config,
            "user_ranks": self.user_ranks
        }
        
        if format == "json":
            return export_data
        elif format == "csv":
            # Convert to CSV format
            csv_data = "user_id,level,xp,rank_name,messages_sent\n"
            for user_id, rank in self.user_ranks.items():
                csv_data += f"{user_id},{rank['level']},{rank['xp']},{rank['rank_name']},{rank['messages_sent']}\n"
            return {"format": "csv", "data": csv_data}
        else:
            return {"error": "Unsupported format"}
            
    async def import_rank_data(self, data: Dict[str, Any]) -> bool:
        """
        Import rank data
        
        Args:
            data: Rank data to import
            
        Returns:
            True if successful
        """
        try:
            if "user_ranks" in data:
                self.user_ranks.update(data["user_ranks"])
                
            if "rank_config" in data:
                self.rank_config.update(data["rank_config"])
                
            self.logger.info(f"📥 Imported rank data for {len(data.get('user_ranks', {}))} users")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error importing rank data: {e}")
            return False