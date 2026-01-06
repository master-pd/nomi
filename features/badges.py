"""
Badge and Achievement System
For rewarding users and encouraging engagement
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from config import Config
from utils.json_utils import JSONManager

logger = logging.getLogger(__name__)
json_manager = JSONManager()

class BadgeType(Enum):
    """Types of badges"""
    WELCOME = "welcome"
    MESSAGING = "messaging"
    ACTIVITY = "activity"
    LOYALTY = "loyalty"
    SOCIAL = "social"
    MODERATION = "moderation"
    SPECIAL = "special"
    ADMIN = "admin"

class BadgeSystem:
    """Professional badge and achievement system"""
    
    def __init__(self):
        self.badges = self._initialize_badges()
        self.user_badges_cache = {}
        
    def _initialize_badges(self) -> Dict[str, Dict]:
        """Initialize all available badges"""
        return {
            # Welcome Badges
            "first_join": {
                "id": "first_join",
                "name": "👋 প্রথম অভ্যর্থনা",
                "description": "প্রথমবার গ্রুপে যোগদান",
                "type": BadgeType.WELCOME,
                "icon": "👋",
                "rarity": "common",
                "points": 10
            },
            "welcome_king": {
                "id": "welcome_king",
                "name": "👑 ওয়েলকাম কিং",
                "description": "১০০ জন নতুন সদস্যকে স্বাগতম জানানো",
                "type": BadgeType.WELCOME,
                "icon": "👑",
                "rarity": "epic",
                "points": 100,
                "requirement": {"welcome_count": 100}
            },
            
            # Messaging Badges
            "first_message": {
                "id": "first_message",
                "name": "💬 প্রথম বার্তা",
                "description": "প্রথম মেসেজ পাঠানো",
                "type": BadgeType.MESSAGING,
                "icon": "💬",
                "rarity": "common",
                "points": 5
            },
            "chatty": {
                "id": "chatty",
                "name": "💭 কথা প্রিয়",
                "description": "৫০টি মেসেজ পাঠানো",
                "type": BadgeType.MESSAGING,
                "icon": "💭",
                "rarity": "uncommon",
                "points": 25,
                "requirement": {"messages_count": 50}
            },
            "conversationalist": {
                "id": "conversationalist",
                "name": "🗣️ কথোপকথনকারী",
                "description": "২৫০টি মেসেজ পাঠানো",
                "type": BadgeType.MESSAGING,
                "icon": "🗣️",
                "rarity": "rare",
                "points": 50,
                "requirement": {"messages_count": 250}
            },
            "message_master": {
                "id": "message_master",
                "name": "📝 মেসেজ মাস্টার",
                "description": "১০০০টি মেসেজ পাঠানো",
                "type": BadgeType.MESSAGING,
                "icon": "📝",
                "rarity": "epic",
                "points": 100,
                "requirement": {"messages_count": 1000}
            },
            "legendary_chatter": {
                "id": "legendary_chatter",
                "name": "🔥 কিংবদন্তি কথক",
                "description": "৫০০০টি মেসেজ পাঠানো",
                "type": BadgeType.MESSAGING,
                "icon": "🔥",
                "rarity": "legendary",
                "points": 500,
                "requirement": {"messages_count": 5000}
            },
            
            # Activity Badges
            "early_bird": {
                "id": "early_bird",
                "name": "🌅 ভোরের পাখি",
                "description": "সকাল ৬-৯টার মধ্যে ৭ দিন একটিভ",
                "type": BadgeType.ACTIVITY,
                "icon": "🌅",
                "rarity": "uncommon",
                "points": 30
            },
            "night_owl": {
                "id": "night_owl",
                "name": "🦉 রাতের পেঁচা",
                "description": "রাত ১০-২টার মধ্যে ৭ দিন একটিভ",
                "type": BadgeType.ACTIVITY,
                "icon": "🦉",
                "rarity": "uncommon",
                "points": 30
            },
            "streak_7": {
                "id": "streak_7",
                "name": "🔥 ৭ দিন স্ট্রিক",
                "description": "৭ দিন ধরে লগইন",
                "type": BadgeType.ACTIVITY,
                "icon": "🔥",
                "rarity": "rare",
                "points": 50
            },
            "streak_30": {
                "id": "streak_30",
                "name": "⚡ ৩০ দিন স্ট্রিক",
                "description": "৩০ দিন ধরে লগইন",
                "type": BadgeType.ACTIVITY,
                "icon": "⚡",
                "rarity": "epic",
                "points": 100
            },
            "streak_100": {
                "id": "streak_100",
                "name": "💎 ১০০ দিন স্ট্রিক",
                "description": "১০০ দিন ধরে লগইন",
                "type": BadgeType.ACTIVITY,
                "icon": "💎",
                "rarity": "legendary",
                "points": 500
            },
            
            # Loyalty Badges
            "one_month": {
                "id": "one_month",
                "name": "🥉 এক মাস",
                "description": "১ মাস গ্রুপের সদস্য",
                "type": BadgeType.LOYALTY,
                "icon": "🥉",
                "rarity": "common",
                "points": 25
            },
            "three_months": {
                "id": "three_months",
                "name": "🥈 তিন মাস",
                "description": "৩ মাস গ্রুপের সদস্য",
                "type": BadgeType.LOYALTY,
                "icon": "🥈",
                "rarity": "uncommon",
                "points": 50
            },
            "six_months": {
                "id": "six_months",
                "name": "🥇 ছয় মাস",
                "description": "৬ মাস গ্রুপের সদস্য",
                "type": BadgeType.LOYALTY,
                "icon": "🥇",
                "rarity": "rare",
                "points": 100
            },
            "one_year": {
                "id": "one_year",
                "name": "🏆 এক বছর",
                "description": "১ বছর গ্রুপের সদস্য",
                "type": BadgeType.LOYALTY,
                "icon": "🏆",
                "rarity": "epic",
                "points": 250
            },
            "veteran": {
                "id": "veteran",
                "name": "🛡️ প্রবীণ সদস্য",
                "description": "২ বছর গ্রুপের সদস্য",
                "type": BadgeType.LOYALTY,
                "icon": "🛡️",
                "rarity": "legendary",
                "points": 500
            },
            
            # Social Badges
            "popular": {
                "id": "popular",
                "name": "⭐ জনপ্রিয়",
                "description": "১০০ রিপুটেশন পয়েন্ট",
                "type": BadgeType.SOCIAL,
                "icon": "⭐",
                "rarity": "rare",
                "points": 50,
                "requirement": {"reputation": 100}
            },
            "influencer": {
                "id": "influencer",
                "name": "🌠 প্রভাবশালী",
                "description": "৫০০ রিপুটেশন পয়েন্ট",
                "type": BadgeType.SOCIAL,
                "icon": "🌠",
                "rarity": "epic",
                "points": 100,
                "requirement": {"reputation": 500}
            },
            "celebrity": {
                "id": "celebrity",
                "name": "🎖️ সেলিব্রিটি",
                "description": "১০০০ রিপুটেশন পয়েন্ট",
                "type": BadgeType.SOCIAL,
                "icon": "🎖️",
                "rarity": "legendary",
                "points": 500,
                "requirement": {"reputation": 1000}
            },
            "helper": {
                "id": "helper",
                "name": "🤝 সাহায্যকারী",
                "description": "৫০ বার সাহায্য করা",
                "type": BadgeType.SOCIAL,
                "icon": "🤝",
                "rarity": "rare",
                "points": 50
            },
            
            # Moderation Badges
            "rule_follower": {
                "id": "rule_follower",
                "name": "📏 নিয়ম অনুসারী",
                "description": "কোনো সতর্কতা ছাড়াই ৩০ দিন",
                "type": BadgeType.MODERATION,
                "icon": "📏",
                "rarity": "uncommon",
                "points": 30
            },
            "peacekeeper": {
                "id": "peacekeeper",
                "name": "🕊️ শান্তিরক্ষক",
                "description": "১০টি রিপোর্ট সমাধান",
                "type": BadgeType.MODERATION,
                "icon": "🕊️",
                "rarity": "rare",
                "points": 50
            },
            
            # Special Badges
            "bug_hunter": {
                "id": "bug_hunter",
                "name": "🐛 বাগ হান্টার",
                "description": "প্রথম বাগ রিপোর্ট করা",
                "type": BadgeType.SPECIAL,
                "icon": "🐛",
                "rarity": "special",
                "points": 100
            },
            "suggestions_king": {
                "id": "suggestions_king",
                "name": "💡 পরামর্শ রাজা",
                "description": "১০টি সুপারিশ গৃহীত হয়েছে",
                "type": BadgeType.SPECIAL,
                "icon": "💡",
                "rarity": "epic",
                "points": 150
            },
            "event_champion": {
                "id": "event_champion",
                "name": "🎯 ইভেন্ট চ্যাম্পিয়ন",
                "description": "৩টি ইভেন্ট জয়ী",
                "type": BadgeType.SPECIAL,
                "icon": "🎯",
                "rarity": "legendary",
                "points": 300
            },
            
            # Admin Badges
            "group_creator": {
                "id": "group_creator",
                "name": "🏗️ গ্রুপ নির্মাতা",
                "description": "গ্রুপ তৈরি করেছেন",
                "type": BadgeType.ADMIN,
                "icon": "🏗️",
                "rarity": "special",
                "points": 200
            },
            "moderator": {
                "id": "moderator",
                "name": "⚖️ মডারেটর",
                "description": "গ্রুপ মডারেটর",
                "type": BadgeType.ADMIN,
                "icon": "⚖️",
                "rarity": "special",
                "points": 150
            },
            "admin": {
                "id": "admin",
                "name": "👑 এডমিন",
                "description": "গ্রুপ এডমিন",
                "type": BadgeType.ADMIN,
                "icon": "👑",
                "rarity": "special",
                "points": 300
            }
        }
    
    def get_user_badges(self, user_id: int) -> List[Dict]:
        """Get all badges earned by a user"""
        try:
            # Check cache first
            cache_key = str(user_id)
            if cache_key in self.user_badges_cache:
                return self.user_badges_cache[cache_key]
            
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return []
            
            badges = user_data.get('badges', [])
            badge_details = []
            
            for badge_id in badges:
                if badge_id in self.badges:
                    badge_details.append(self.badges[badge_id])
            
            # Cache the result
            self.user_badges_cache[cache_key] = badge_details
            
            return badge_details
            
        except Exception as e:
            logger.error(f"Error getting user badges: {e}")
            return []
    
    def check_and_award_badges(self, user_id: int, action_type: str, data: Dict = None) -> List[Dict]:
        """
        Check and award badges based on user actions
        Returns list of newly awarded badges
        """
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return []
            
            newly_awarded = []
            
            # Check different badge categories based on action
            if action_type == "message_sent":
                newly_awarded.extend(self._check_messaging_badges(user_data))
                newly_awarded.extend(self._check_activity_badges(user_data))
                
            elif action_type == "user_joined":
                newly_awarded.extend(self._check_welcome_badges(user_data))
                
            elif action_type == "reputation_earned":
                newly_awarded.extend(self._check_social_badges(user_data))
                
            elif action_type == "day_passed":
                newly_awarded.extend(self._check_loyalty_badges(user_data))
                newly_awarded.extend(self._check_streak_badges(user_data))
            
            elif action_type == "moderation_action":
                newly_awarded.extend(self._check_moderation_badges(user_data, data))
            
            # Add any special badge checks
            newly_awarded.extend(self._check_special_badges(user_data, action_type, data))
            
            # Award the badges
            for badge in newly_awarded:
                self._award_badge(user_id, badge["id"])
            
            return newly_awarded
            
        except Exception as e:
            logger.error(f"Error checking badges: {e}")
            return []
    
    def _check_messaging_badges(self, user_data: Dict) -> List[Dict]:
        """Check for messaging-related badges"""
        messages_count = user_data.get('messages_count', 0)
        badges_to_award = []
        
        # Check message count badges
        thresholds = [
            (50, "chatty"),
            (250, "conversationalist"),
            (1000, "message_master"),
            (5000, "legendary_chatter")
        ]
        
        for threshold, badge_id in thresholds:
            if messages_count >= threshold:
                if badge_id not in user_data.get('badges', []):
                    badges_to_award.append(self.badges[badge_id])
        
        return badges_to_award
    
    def _check_welcome_badges(self, user_data: Dict) -> List[Dict]:
        """Check for welcome-related badges"""
        badges_to_award = []
        
        # First join badge
        if "first_join" not in user_data.get('badges', []):
            badges_to_award.append(self.badges["first_join"])
        
        # Welcome count badge
        welcome_count = user_data.get('welcome_count', 0)
        if welcome_count >= 100 and "welcome_king" not in user_data.get('badges', []):
            badges_to_award.append(self.badges["welcome_king"])
        
        return badges_to_award
    
    def _check_activity_badges(self, user_data: Dict) -> List[Dict]:
        """Check for activity-related badges"""
        badges_to_award = []
        
        # Check first message badge
        if user_data.get('messages_count', 0) >= 1 and "first_message" not in user_data.get('badges', []):
            badges_to_award.append(self.badges["first_message"])
        
        # Check streak badges (simplified)
        current_streak = user_data.get('current_streak', 0)
        streak_thresholds = [(7, "streak_7"), (30, "streak_30"), (100, "streak_100")]
        
        for days, badge_id in streak_thresholds:
            if current_streak >= days and badge_id not in user_data.get('badges', []):
                badges_to_award.append(self.badges[badge_id])
        
        return badges_to_award
    
    def _check_loyalty_badges(self, user_data: Dict) -> List[Dict]:
        """Check for loyalty badges based on join duration"""
        badges_to_award = []
        
        join_date_str = user_data.get('join_date')
        if not join_date_str:
            return badges_to_award
        
        try:
            join_date = datetime.fromisoformat(join_date_str)
            current_date = datetime.now()
            days_in_group = (current_date - join_date).days
            
            loyalty_thresholds = [
                (30, "one_month"),
                (90, "three_months"),
                (180, "six_months"),
                (365, "one_year"),
                (730, "veteran")
            ]
            
            for days, badge_id in loyalty_thresholds:
                if days_in_group >= days and badge_id not in user_data.get('badges', []):
                    badges_to_award.append(self.badges[badge_id])
                    
        except Exception as e:
            logger.error(f"Error checking loyalty badges: {e}")
        
        return badges_to_award
    
    def _check_streak_badges(self, user_data: Dict) -> List[Dict]:
        """Check streak-related badges"""
        # This would track daily login streaks
        # For now, returning empty list
        return []
    
    def _check_social_badges(self, user_data: Dict) -> List[Dict]:
        """Check social/reputation badges"""
        badges_to_award = []
        reputation = user_data.get('reputation', 0)
        
        reputation_thresholds = [
            (100, "popular"),
            (500, "influencer"),
            (1000, "celebrity")
        ]
        
        for threshold, badge_id in reputation_thresholds:
            if reputation >= threshold and badge_id not in user_data.get('badges', []):
                badges_to_award.append(self.badges[badge_id])
        
        return badges_to_award
    
    def _check_moderation_badges(self, user_data: Dict, data: Dict) -> List[Dict]:
        """Check moderation-related badges"""
        badges_to_award = []
        
        # Check rule follower (no warnings for 30 days)
        last_warning = user_data.get('last_warning_date')
        if last_warning:
            try:
                last_warning_date = datetime.fromisoformat(last_warning)
                days_without_warning = (datetime.now() - last_warning_date).days
                
                if days_without_warning >= 30 and "rule_follower" not in user_data.get('badges', []):
                    badges_to_award.append(self.badges["rule_follower"])
                    
            except Exception:
                pass
        
        return badges_to_award
    
    def _check_special_badges(self, user_data: Dict, action_type: str, data: Dict) -> List[Dict]:
        """Check special badges based on various criteria"""
        badges_to_award = []
        
        # Special badge logic would go here
        # For example, based on admin status, special events, etc.
        
        return badges_to_award
    
    def _award_badge(self, user_id: int, badge_id: str):
        """Award a badge to a user"""
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return False
            
            badges = user_data.get('badges', [])
            
            if badge_id not in badges:
                badges.append(badge_id)
                user_data['badges'] = badges
                user_data['badge_points'] = user_data.get('badge_points', 0) + self.badges[badge_id]['points']
                user_data['last_badge_awarded'] = datetime.now().isoformat()
                
                # Update user
                json_manager.update_user(user_id, user_data)
                
                # Clear cache
                cache_key = str(user_id)
                if cache_key in self.user_badges_cache:
                    del self.user_badges_cache[cache_key]
                
                logger.info(f"Awarded badge {badge_id} to user {user_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error awarding badge: {e}")
            return False
    
    def get_badge_progress(self, user_id: int, badge_id: str) -> Dict:
        """Get progress towards a specific badge"""
        try:
            if badge_id not in self.badges:
                return {"error": "Badge not found"}
            
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return {"error": "User not found"}
            
            badge = self.badges[badge_id]
            requirement = badge.get('requirement')
            
            if not requirement:
                return {
                    "badge": badge,
                    "earned": badge_id in user_data.get('badges', []),
                    "progress": 100,
                    "description": "Special badge"
                }
            
            # Calculate progress based on requirement
            progress_data = {}
            
            for key, target in requirement.items():
                current = user_data.get(key, 0)
                progress = min((current / target) * 100, 100) if target > 0 else 100
                
                progress_data[key] = {
                    "current": current,
                    "target": target,
                    "progress": progress,
                    "remaining": max(target - current, 0)
                }
            
            overall_progress = sum(p["progress"] for p in progress_data.values()) / len(progress_data)
            
            return {
                "badge": badge,
                "earned": badge_id in user_data.get('badges', []),
                "progress": overall_progress,
                "details": progress_data,
                "remaining_tasks": [
                    f"{key}: {data['current']}/{data['target']}"
                    for key, data in progress_data.items()
                    if data['current'] < data['target']
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting badge progress: {e}")
            return {"error": str(e)}
    
    def get_available_badges(self) -> List[Dict]:
        """Get all available badges"""
        return list(self.badges.values())
    
    def get_badges_by_type(self, badge_type: BadgeType) -> List[Dict]:
        """Get badges by type"""
        return [badge for badge in self.badges.values() if badge['type'] == badge_type]
    
    def get_rarity_stats(self) -> Dict:
        """Get statistics about badge rarity"""
        stats = {
            "total_badges": len(self.badges),
            "by_rarity": {},
            "by_type": {},
            "total_points": sum(badge['points'] for badge in self.badges.values())
        }
        
        # Count by rarity
        for badge in self.badges.values():
            rarity = badge['rarity']
            stats["by_rarity"][rarity] = stats["by_rarity"].get(rarity, 0) + 1
        
        # Count by type
        for badge in self.badges.values():
            badge_type = badge['type'].value
            stats["by_type"][badge_type] = stats["by_type"].get(badge_type, 0) + 1
        
        return stats
    
    def get_user_badge_stats(self, user_id: int) -> Dict:
        """Get user badge statistics"""
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return {"error": "User not found"}
            
            badges = self.get_user_badges(user_id)
            total_points = user_data.get('badge_points', 0)
            
            # Count by rarity
            by_rarity = {}
            by_type = {}
            
            for badge in badges:
                rarity = badge['rarity']
                badge_type = badge['type'].value
                
                by_rarity[rarity] = by_rarity.get(rarity, 0) + 1
                by_type[badge_type] = by_type.get(badge_type, 0) + 1
            
            # Calculate completion percentage
            total_badges = len(self.badges)
            earned_badges = len(badges)
            completion_rate = (earned_badges / total_badges * 100) if total_badges > 0 else 0
            
            # Get next achievable badges
            next_badges = self._get_next_achievable_badges(user_data)
            
            return {
                "total_earned": earned_badges,
                "total_available": total_badges,
                "completion_rate": completion_rate,
                "total_points": total_points,
                "by_rarity": by_rarity,
                "by_type": by_type,
                "next_badges": next_badges,
                "recent_badges": badges[-5:] if badges else []
            }
            
        except Exception as e:
            logger.error(f"Error getting user badge stats: {e}")
            return {"error": str(e)}
    
    def _get_next_achievable_badges(self, user_data: Dict) -> List[Dict]:
        """Get badges that user is close to earning"""
        next_badges = []
        
        for badge_id, badge in self.badges.items():
            if badge_id in user_data.get('badges', []):
                continue
            
            requirement = badge.get('requirement')
            if not requirement:
                continue
            
            # Check if user is making progress
            progress_data = {}
            total_progress = 0
            
            for key, target in requirement.items():
                current = user_data.get(key, 0)
                progress = min((current / target) * 100, 100) if target > 0 else 0
                progress_data[key] = progress
                total_progress += progress
            
            avg_progress = total_progress / len(requirement)
            
            # If progress is more than 50%, include in next badges
            if avg_progress >= 50:
                badge_with_progress = badge.copy()
                badge_with_progress['progress'] = avg_progress
                badge_with_progress['progress_details'] = progress_data
                next_badges.append(badge_with_progress)
        
        # Sort by progress (descending)
        next_badges.sort(key=lambda x: x['progress'], reverse=True)
        
        return next_badges[:5]  # Return top 5
    
    def award_admin_badge(self, user_id: int, badge_id: str) -> bool:
        """Award an admin badge (special badges that require manual awarding)"""
        try:
            # Check if it's an admin badge
            if badge_id not in self.badges:
                return False
            
            badge = self.badges[badge_id]
            if badge['type'] != BadgeType.ADMIN:
                return False
            
            return self._award_badge(user_id, badge_id)
            
        except Exception as e:
            logger.error(f"Error awarding admin badge: {e}")
            return False
    
    def remove_badge(self, user_id: int, badge_id: str) -> bool:
        """Remove a badge from a user"""
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return False
            
            badges = user_data.get('badges', [])
            
            if badge_id in badges:
                badges.remove(badge_id)
                user_data['badges'] = badges
                
                # Subtract points
                if badge_id in self.badges:
                    user_data['badge_points'] = max(user_data.get('badge_points', 0) - self.badges[badge_id]['points'], 0)
                
                json_manager.update_user(user_id, user_data)
                
                # Clear cache
                cache_key = str(user_id)
                if cache_key in self.user_badges_cache:
                    del self.user_badges_cache[cache_key]
                
                logger.info(f"Removed badge {badge_id} from user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing badge: {e}")
            return False
    
    def generate_badge_card(self, user_id: int) -> Dict:
        """Generate badge showcase card"""
        try:
            user_data = json_manager.get_user(user_id)
            if not user_data:
                return {"error": "User not found"}
            
            badges = self.get_user_badges(user_id)
            stats = self.get_user_badge_stats(user_id)
            
            # Group badges by type
            badges_by_type = {}
            for badge in badges:
                badge_type = badge['type'].value
                if badge_type not in badges_by_type:
                    badges_by_type[badge_type] = []
                badges_by_type[badge_type].append(badge)
            
            # Get top 3 badges by points
            top_badges = sorted(badges, key=lambda x: x['points'], reverse=True)[:3]
            
            return {
                "user_info": {
                    "user_id": user_id,
                    "name": user_data.get('first_name', 'Unknown'),
                    "badge_points": user_data.get('badge_points', 0)
                },
                "stats": stats,
                "top_badges": top_badges,
                "badges_by_type": badges_by_type,
                "next_goals": stats.get('next_badges', []),
                "showcase_url": f"/badges/showcase/{user_id}"  # Placeholder for actual URL
            }
            
        except Exception as e:
            logger.error(f"Error generating badge card: {e}")
            return {"error": str(e)}
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get badge points leaderboard"""
        try:
            all_users = json_manager.get_all_users()
            
            # Filter users with badge points
            users_with_points = [
                {
                    "user_id": user.get('user_id'),
                    "name": user.get('first_name', 'Unknown'),
                    "badge_points": user.get('badge_points', 0),
                    "badge_count": len(user.get('badges', [])),
                    "rank": user.get('rank', 'নতুন')
                }
                for user in all_users
                if user.get('badge_points', 0) > 0
            ]
            
            # Sort by points (descending)
            users_with_points.sort(key=lambda x: x['badge_points'], reverse=True)
            
            # Add position
            for i, user in enumerate(users_with_points[:limit], start=1):
                user['position'] = i
            
            return users_with_points[:limit]
            
        except Exception as e:
            logger.error(f"Error getting badge leaderboard: {e}")
            return []