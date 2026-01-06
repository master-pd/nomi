"""
Professional Auto-Moderation System
With spam detection, flood control, link filtering, and more
"""

import re
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from aiogram import Bot
from aiogram.types import Message, User

from config import Config
from utils.json_utils import JSONManager
from utils.logger_utils import setup_logger

logger = setup_logger("moderation")
json_manager = JSONManager()

class ModerationSystem:
    """Professional auto-moderation system"""
    
    def __init__(self):
        # User message tracking for flood detection
        self.user_messages = defaultdict(list)
        
        # Spam detection
        self.spam_patterns = [
            r'(?i)buy.*followers',
            r'(?i)earn.*money.*fast',
            r'(?i)free.*bitcoin',
            r'(?i)click.*link',
            r'(?i)join.*channel',
            r'(?i)promote.*channel',
            r'(?i)increase.*view',
            r'(?i)sex.*video',
            r'(?i)porn',
            r'(?i)adult.*content',
            r'(?i)viagra',
            r'(?i)casino',
            r'(?i)betting',
            r'(?i)lottery'
        ]
        
        # Compiled regex patterns
        self.spam_regex = [re.compile(pattern) for pattern in self.spam_patterns]
        
        # Bad words list (Bangla)
        self.bad_words = self._load_bad_words()
        
        # Allowed domains
        self.allowed_domains = [
            'youtube.com', 'youtu.be',
            'twitter.com', 'x.com',
            'facebook.com', 'fb.com',
            'instagram.com',
            'github.com',
            'telegram.org', 't.me',
            'google.com', 'drive.google.com',
            'wikipedia.org',
            'stackoverflow.com',
            'reddit.com',
            'discord.com',
            'medium.com'
        ]
        
        # Warning system
        self.user_warnings = defaultdict(int)
        
        # Cooldown periods
        self.cooldowns = {
            'warn': 300,  # 5 minutes
            'mute': 900,  # 15 minutes
            'kick': 3600,  # 1 hour
            'ban': 86400  # 24 hours
        }
    
    def _load_bad_words(self) -> Set[str]:
        """Load bad words list"""
        # In production, load from file or database
        # This is a sample list
        bad_words = {
            # Bangla bad words
            'গালি', 'খারাপ', 'অশ্লীল', 'অভদ্র',
            # English bad words
            'fuck', 'shit', 'bastard', 'asshole', 'bitch',
            'damn', 'hell', 'crap', 'dick', 'pussy'
        }
        
        return bad_words
    
    async def check_message(self, message: Message) -> Dict:
        """
        Check message for violations
        Returns dict with action_required and action type
        """
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            text = message.text or message.caption or ""
            
            # Skip if message is from admin
            if user_id in Config.ADMIN_IDS:
                return {"action_required": False}
            
            # Check message length (too long might be spam)
            if len(text) > 2000:
                logger.info(f"Long message detected from {user_id}")
                return {
                    "action_required": True,
                    "action": "warn",
                    "reason": "message_too_long"
                }
            
            # Check for flood
            if self._check_flood(user_id, chat_id):
                logger.warning(f"Flood detected from {user_id}")
                return {
                    "action_required": True,
                    "action": "mute",
                    "reason": "flooding"
                }
            
            # Check for spam
            if self._check_spam(text):
                logger.warning(f"Spam detected from {user_id}")
                return {
                    "action_required": True,
                    "action": "delete",
                    "reason": "spam"
                }
            
            # Check for bad words
            if self._check_bad_words(text):
                logger.warning(f"Bad words detected from {user_id}")
                return {
                    "action_required": True,
                    "action": "warn",
                    "reason": "bad_words"
                }
            
            # Check for links
            if self._check_links(text):
                logger.warning(f"Unauthorized links from {user_id}")
                return {
                    "action_required": True,
                    "action": "delete",
                    "reason": "unauthorized_links"
                }
            
            # Check for excessive capital letters
            if self._check_caps(text):
                logger.info(f"Excessive caps from {user_id}")
                return {
                    "action_required": True,
                    "action": "warn",
                    "reason": "excessive_caps"
                }
            
            # Check for repeated messages
            if self._check_repetition(user_id, text):
                logger.warning(f"Repeated messages from {user_id}")
                return {
                    "action_required": True,
                    "action": "mute",
                    "reason": "repetition"
                }
            
            # Check warning count
            warnings = self.user_warnings.get(user_id, 0)
            if warnings >= Config.MAX_WARNINGS:
                logger.warning(f"Max warnings reached for {user_id}")
                return {
                    "action_required": True,
                    "action": "mute",
                    "reason": "max_warnings"
                }
            
            return {"action_required": False}
            
        except Exception as e:
            logger.error(f"Error in check_message: {e}")
            return {"action_required": False}
    
    def _check_flood(self, user_id: int, chat_id: int) -> bool:
        """
        Check if user is flooding messages
        """
        try:
            current_time = time.time()
            key = f"{user_id}_{chat_id}"
            
            # Clean old messages
            self.user_messages[key] = [
                msg_time for msg_time in self.user_messages[key]
                if current_time - msg_time < Config.FLOOD_WINDOW_SECONDS
            ]
            
            # Add current message
            self.user_messages[key].append(current_time)
            
            # Check if exceeds limit
            if len(self.user_messages[key]) > Config.MAX_MESSAGES_PER_MINUTE:
                # Reset for this user
                self.user_messages[key] = []
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in flood check: {e}")
            return False
    
    def _check_spam(self, text: str) -> bool:
        """
        Check if text contains spam patterns
        """
        try:
            text_lower = text.lower()
            
            # Check against regex patterns
            for pattern in self.spam_regex:
                if pattern.search(text_lower):
                    return True
            
            # Check for excessive special characters
            special_chars = re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', text)
            if len(special_chars) > len(text) * 0.3:  # More than 30% special chars
                return True
            
            # Check for excessive numbers (like phone numbers)
            numbers = re.findall(r'\d+', text)
            total_digits = sum(len(num) for num in numbers)
            if total_digits > 15:  # More than 15 digits
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in spam check: {e}")
            return False
    
    def _check_bad_words(self, text: str) -> bool:
        """
        Check if text contains bad words
        """
        try:
            text_lower = text.lower()
            
            # Check each bad word
            for word in self.bad_words:
                if word.lower() in text_lower:
                    # Check if it's part of another word
                    pattern = r'\b' + re.escape(word) + r'\b'
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in bad words check: {e}")
            return False
    
    def _check_links(self, text: str) -> bool:
        """
        Check for unauthorized links
        """
        try:
            # Find all URLs
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .\-?&=%#]*'
            urls = re.findall(url_pattern, text)
            
            if not urls:
                return False
            
            for url in urls:
                # Extract domain
                domain_match = re.search(r'https?://([^/]+)', url)
                if domain_match:
                    domain = domain_match.group(1).lower()
                    
                    # Remove www. prefix
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    # Check if domain is allowed
                    is_allowed = False
                    for allowed in self.allowed_domains:
                        if domain == allowed or domain.endswith('.' + allowed):
                            is_allowed = True
                            break
                    
                    if not is_allowed:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in link check: {e}")
            return False
    
    def _check_caps(self, text: str) -> bool:
        """
        Check for excessive capital letters
        """
        try:
            if not text:
                return False
            
            # Count capital letters
            caps_count = sum(1 for char in text if char.isupper())
            total_chars = len(text)
            
            # If more than 70% are caps and message is long enough
            if total_chars > 10 and caps_count / total_chars > 0.7:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in caps check: {e}")
            return False
    
    def _check_repetition(self, user_id: int, text: str) -> bool:
        """
        Check for repeated messages
        """
        try:
            # Store last few messages per user
            if not hasattr(self, 'user_last_messages'):
                self.user_last_messages = defaultdict(list)
            
            # Clean old messages
            max_messages = 5
            self.user_last_messages[user_id] = self.user_last_messages[user_id][-max_messages:]
            
            # Check if current message is similar to previous ones
            for prev_text in self.user_last_messages[user_id]:
                if self._similarity(text, prev_text) > 0.8:  # 80% similarity
                    return True
            
            # Add current message
            self.user_last_messages[user_id].append(text)
            
            return False
            
        except Exception as e:
            logger.error(f"Error in repetition check: {e}")
            return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity (simplified)
        """
        if not text1 or not text2:
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union
    
    async def apply_action(self, bot: Bot, message: Message, action: str, reason: str):
        """
        Apply moderation action
        """
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            user_name = message.from_user.first_name
            
            action_messages = {
                "warn": f"⚠️ সতর্কতা: {user_name}, আপনি {reason} এর জন্য সতর্ক হয়েছেন।",
                "delete": "🗑️ মেসেজ ডিলিট করা হয়েছে",
                "mute": f"🔇 {user_name} কে মিউট করা হয়েছে ({reason})",
                "kick": f"👢 {user_name} কে কিক করা হয়েছে",
                "ban": f"🚫 {user_name} কে ব্যান করা হয়েছে"
            }
            
            # Log the action
            json_manager.log_action(
                action_type=action,
                user_id=user_id,
                details={
                    "chat_id": chat_id,
                    "reason": reason,
                    "message_id": message.message_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Update warning count
            if action == "warn":
                self.user_warnings[user_id] = self.user_warnings.get(user_id, 0) + 1
                
                warning_message = f"""
                ⚠️ **সতর্কতা**
                
                **ইউজার:** {user_name}
                **কারণ:** {self._get_reason_text(reason)}
                **সতর্কতা:** {self.user_warnings[user_id]}/{Config.MAX_WARNINGS}
                
                পরবর্তী সতর্কতায় মিউট করা হবে।
                """
                
                await message.answer(warning_message, parse_mode="Markdown")
            
            elif action == "delete":
                await message.delete()
                await message.answer("❌ মেসেজ ডিলিট করা হয়েছে (নিয়ম ভঙ্গ)")
            
            elif action == "mute":
                # Implement mute logic
                # Note: Bot needs proper permissions
                try:
                    # For demonstration - in production, use proper mute method
                    mute_message = f"""
                    🔇 **মিউট নোটিশ**
                    
                    **ইউজার:** {user_name}
                    **কারণ:** {self._get_reason_text(reason)}
                    **সময়:** 15 মিনিট
                    
                    মিউট শেষ হওয়ার পরে আবার কথা বলতে পারবেন।
                    """
                    
                    await message.answer(mute_message, parse_mode="Markdown")
                    
                    # Reset warnings after mute
                    self.user_warnings[user_id] = 0
                    
                except Exception as e:
                    logger.error(f"Error applying mute: {e}")
                    await message.answer("❌ মিউট করতে পারিনি (পারমিশন চেক করুন)")
            
            # Log to database
            self._log_moderation_action(user_id, action, reason)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying action {action}: {e}")
            return False
    
    def _get_reason_text(self, reason: str) -> str:
        """Convert reason code to Bangla text"""
        reasons = {
            "message_too_long": "খুব লম্বা মেসেজ",
            "flooding": "অতিরিক্ত মেসেজ পাঠানো",
            "spam": "স্প্যাম কন্টেন্ট",
            "bad_words": "অশ্লীল ভাষা",
            "unauthorized_links": "অননুমোদিত লিংক",
            "excessive_caps": "অতিরিক্ত ক্যাপিটাল লেটার",
            "repetition": "একই মেসেজ বারবার পাঠানো",
            "max_warnings": "সর্বোচ্চ সতর্কতা"
        }
        
        return reasons.get(reason, reason)
    
    def _log_moderation_action(self, user_id: int, action: str, reason: str):
        """Log moderation action to database"""
        try:
            # Get user data
            user_data = json_manager.get_user(user_id) or {}
            
            # Update user stats
            user_data['moderation_actions'] = user_data.get('moderation_actions', [])
            user_data['moderation_actions'].append({
                'action': action,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            
            user_data['warning_count'] = self.user_warnings.get(user_id, 0)
            
            json_manager.update_user(user_id, user_data)
            
        except Exception as e:
            logger.error(f"Error logging moderation action: {e}")
    
    async def check_user_join(self, user: User, chat_id: int) -> Dict:
        """
        Check new user for potential spam/bot accounts
        """
        try:
            checks = {
                "is_bot": user.is_bot,
                "no_profile_photo": not user.photo,
                "recent_account": self._is_recent_account(user.id),
                "suspicious_username": self._is_suspicious_username(user.username),
                "suspicious_name": self._is_suspicious_name(user.first_name, user.last_name)
            }
            
            # Calculate risk score
            risk_score = sum(1 for check in checks.values() if check)
            
            if risk_score >= 3:
                return {
                    "action_required": True,
                    "action": "restrict",
                    "reason": "suspicious_account",
                    "risk_score": risk_score,
                    "checks_failed": [k for k, v in checks.items() if v]
                }
            
            return {
                "action_required": False,
                "risk_score": risk_score
            }
            
        except Exception as e:
            logger.error(f"Error in user join check: {e}")
            return {"action_required": False}
    
    def _is_recent_account(self, user_id: int) -> bool:
        """
        Check if account is recently created
        """
        try:
            # Telegram user IDs increase over time
            # Newer accounts have higher IDs
            # This is a simplified check
            current_time = int(time.time())
            user_creation_estimate = (user_id >> 32)  # Rough estimate
            
            # If account appears to be less than 7 days old
            account_age = current_time - user_creation_estimate
            return account_age < 604800  # 7 days in seconds
            
        except:
            return False
    
    def _is_suspicious_username(self, username: str) -> bool:
        """
        Check for suspicious username patterns
        """
        if not username:
            return False
        
        suspicious_patterns = [
            r'bot\d+$',
            r'user\d+$',
            r'spam',
            r'fake',
            r'clone',
            r'test',
            r'admin\d+',
            r'support\d+'
        ]
        
        username_lower = username.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, username_lower):
                return True
        
        # Check for excessive numbers
        numbers = re.findall(r'\d', username)
        if len(numbers) > len(username) * 0.5:  # More than 50% numbers
            return True
        
        return False
    
    def _is_suspicious_name(self, first_name: str, last_name: str) -> bool:
        """
        Check for suspicious name patterns
        """
        full_name = f"{first_name or ''} {last_name or ''}".strip()
        
        if not full_name:
            return True
        
        # Check for generic names
        generic_names = [
            'user', 'user user', 'telegram user', 'tg user',
            'user bot', 'test user', 'new user', 'unknown'
        ]
        
        if full_name.lower() in generic_names:
            return True
        
        # Check for emoji-only names
        import emoji
        if emoji.emoji_count(full_name) > 2:
            return True
        
        # Check for excessive special characters
        special_chars = re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', full_name)
        if len(special_chars) > 3:
            return True
        
        return False
    
    def get_moderation_stats(self, chat_id: int = None) -> Dict:
        """
        Get moderation statistics
        """
        try:
            stats = {
                "total_actions": 0,
                "actions_by_type": defaultdict(int),
                "recent_actions": [],
                "top_offenders": [],
                "warning_distribution": defaultdict(int)
            }
            
            # Get all users
            users = json_manager.get_all_users()
            
            for user in users:
                actions = user.get('moderation_actions', [])
                stats["total_actions"] += len(actions)
                
                # Count by action type
                for action in actions:
                    action_type = action.get('action', 'unknown')
                    stats["actions_by_type"][action_type] += 1
                
                # Get warning count
                warnings = user.get('warning_count', 0)
                stats["warning_distribution"][warnings] += 1
                
                # Add to top offenders if has actions
                if actions:
                    stats["top_offenders"].append({
                        'user_id': user.get('user_id'),
                        'name': user.get('first_name', 'Unknown'),
                        'actions_count': len(actions),
                        'last_action': actions[-1].get('timestamp') if actions else None
                    })
            
            # Sort top offenders
            stats["top_offenders"].sort(key=lambda x: x['actions_count'], reverse=True)
            stats["top_offenders"] = stats["top_offenders"][:10]
            
            # Get recent actions from logs
            recent_actions = json_manager.get_recent_actions(limit=20)
            stats["recent_actions"] = recent_actions
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting moderation stats: {e}")
            return {}
    
    def reset_user_warnings(self, user_id: int) -> bool:
        """
        Reset warning count for user
        """
        try:
            if user_id in self.user_warnings:
                self.user_warnings[user_id] = 0
                
                # Update database
                user_data = json_manager.get_user(user_id) or {}
                user_data['warning_count'] = 0
                json_manager.update_user(user_id, user_data)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error resetting warnings: {e}")
            return False
    
    def cleanup_old_data(self, older_than_days: int = 30):
        """
        Cleanup old moderation data
        """
        try:
            current_time = time.time()
            cutoff = older_than_days * 86400
            
            # Clean old message tracking
            for key in list(self.user_messages.keys()):
                # Keep only recent entries
                self.user_messages[key] = [
                    t for t in self.user_messages[key]
                    if current_time - t < cutoff
                ]
                
                # Remove empty lists
                if not self.user_messages[key]:
                    del self.user_messages[key]
            
            # Clean old last messages
            if hasattr(self, 'user_last_messages'):
                for user_id in list(self.user_last_messages.keys()):
                    # Keep only last 5 messages
                    self.user_last_messages[user_id] = self.user_last_messages[user_id][-5:]
            
            logger.info("Cleaned up old moderation data")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")