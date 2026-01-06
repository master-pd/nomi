"""
Anti-Badword System - Filters inappropriate content
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class FilterAction(Enum):
    """Actions to take on badword detection"""
    DELETE = "delete"
    WARN = "warn"
    MUTE = "mute"
    BAN = "ban"
    REPLACE = "replace"

@dataclass
class BadwordMatch:
    """Badword match result"""
    word: str
    severity: int
    action: FilterAction
    category: str
    position: tuple

class AntiBadword:
    """Anti-badword filtering system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_antibadword")
        self.badwords = set()
        self.badword_patterns = []
        self.whitelist_words = set()
        self.user_warnings = {}
        self.word_categories = {}
        
        # Default configuration
        self.config = {
            "enabled": True,
            "strict_mode": False,
            "auto_delete": True,
            "warn_user": True,
            "mute_on_repeat": True,
            "mute_duration": 600,
            "warning_limit": 3,
            "replace_with": "***",
            "check_variations": True,
            "categories": {
                "offensive": {"severity": 10, "action": "mute"},
                "abusive": {"severity": 9, "action": "mute"},
                "sexual": {"severity": 10, "action": "delete"},
                "racist": {"severity": 10, "action": "ban"},
                "spam": {"severity": 5, "action": "warn"},
                "scam": {"severity": 8, "action": "mute"}
            }
        }
        
        # Initialize default badwords
        self._initialize_default_badwords()
        
    def _initialize_default_badwords(self):
        """Initialize default badword lists"""
        # Note: These are examples. In production, you'd load from a file
        
        # Bengali badwords (placeholder -实际使用时需要更全面的列表)
        bengali_badwords = [
            "খারাপশব্দ", "অপশব্দ", "গালি"
        ]
        
        # English badwords (common)
        english_badwords = [
            "badword", "offensive", "abusive"
        ]
        
        # Add to badwords set
        self.badwords.update(bengali_badwords)
        self.badwords.update(english_boodwords)
        
        # Create patterns for common variations
        self._create_patterns()
        
    def _create_patterns(self):
        """Create regex patterns for badword detection"""
        # Pattern for character replacement (e.g., a -> @, o -> 0)
        self.badword_patterns = []
        
        # For each badword, create pattern with common obfuscations
        for word in self.badwords:
            # Convert to pattern with character variations
            pattern = self._word_to_pattern(word)
            self.badword_patterns.append((pattern, word))
            
    def _word_to_pattern(self, word: str) -> str:
        """Convert word to regex pattern with common obfuscations"""
        # Character substitution mapping
        char_map = {
            'a': '[a@4]',
            'b': '[b8]',
            'c': '[c\(]',
            'e': '[e3]',
            'g': '[g9]',
            'i': '[i1!]',
            'l': '[l1|]',
            'o': '[o0]',
            's': '[s$5]',
            't': '[t7]',
            'z': '[z2]',
            '0': '[o0]',
            '1': '[i1l]',
            '3': '[e3]',
            '4': '[a4]',
            '5': '[s5]',
            '7': '[t7]',
            '8': '[b8]',
            '9': '[g9]'
        }
        
        pattern_parts = []
        for char in word.lower():
            if char in char_map:
                pattern_parts.append(char_map[char])
            else:
                pattern_parts.append(re.escape(char))
                
        # Allow optional characters between letters
        pattern = r'\b' + r'\W*'.join(pattern_parts) + r'\b'
        return pattern
        
    async def check_message(self, message: str, user_id: int,
                          group_id: Optional[int] = None) -> List[BadwordMatch]:
        """
        Check message for badwords
        
        Args:
            message: Message text
            user_id: User ID
            group_id: Group ID
            
        Returns:
            List of badword matches
        """
        if not self.config["enabled"]:
            return []
            
        matches = []
        
        # Normalize message
        normalized = self._normalize_text(message)
        
        # Check against badword list
        found_words = await self._find_badwords(normalized)
        
        for word, position in found_words:
            # Get word category and severity
            category, severity = self._categorize_word(word)
            action_str = self.config["categories"].get(category, {}).get("action", "warn")
            action = FilterAction(action_str)
            
            matches.append(BadwordMatch(
                word=word,
                severity=severity,
                action=action,
                category=category,
                position=position
            ))
            
        # Record warnings for user
        if matches:
            await self._record_user_warning(user_id, group_id, matches)
            
        return matches
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for checking"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
        
    async def _find_badwords(self, text: str) -> List[tuple]:
        """Find badwords in text"""
        found = []
        
        # Check against exact words
        words = text.split()
        for i, word in enumerate(words):
            if word in self.badwords:
                found.append((word, (i, i+1)))
            elif word in self.whitelist_words:
                continue
                
        # Check against patterns (for obfuscated words)
        for pattern, original_word in self.badword_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found.append((original_word, (match.start(), match.end())))
                
        # Remove duplicates
        unique_found = []
        seen = set()
        for word, pos in found:
            if (word, pos) not in seen:
                seen.add((word, pos))
                unique_found.append((word, pos))
                
        return unique_found
        
    def _categorize_word(self, word: str) -> tuple:
        """Categorize word and get severity"""
        # Default category and severity
        default_category = "offensive"
        default_severity = 5
        
        # Check if word has specific category
        if word in self.word_categories:
            category_data = self.word_categories[word]
            return category_data.get("category", default_category), \
                   category_data.get("severity", default_severity)
                   
        # Try to determine category from word properties
        if any(char in word for char in "@#$%&*"):
            return "obfuscated", 6
            
        return default_category, default_severity
        
    async def _record_user_warning(self, user_id: int, group_id: Optional[int],
                                 matches: List[BadwordMatch]):
        """Record warning for user"""
        user_key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if user_key not in self.user_warnings:
            self.user_warnings[user_key] = {
                "count": 0,
                "last_warning": None,
                "words_used": set(),
                "total_severity": 0
            }
            
        user_data = self.user_warnings[user_key]
        user_data["count"] += 1
        user_data["last_warning"] = datetime.now().isoformat()
        
        for match in matches:
            user_data["words_used"].add(match.word)
            user_data["total_severity"] += match.severity
            
    async def get_user_warnings(self, user_id: int,
                              group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get user warning statistics"""
        user_key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if user_key not in self.user_warnings:
            return {
                "user_id": user_id,
                "group_id": group_id,
                "warning_count": 0,
                "words_used": [],
                "total_severity": 0
            }
            
        user_data = self.user_warnings[user_key]
        
        return {
            "user_id": user_id,
            "group_id": group_id,
            "warning_count": user_data["count"],
            "words_used": list(user_data["words_used"]),
            "total_severity": user_data["total_severity"],
            "last_warning": user_data["last_warning"],
            "exceeds_limit": user_data["count"] >= self.config["warning_limit"]
        }
        
    async def reset_user_warnings(self, user_id: int,
                                group_id: Optional[int] = None) -> bool:
        """Reset warnings for user"""
        user_key = f"{user_id}_{group_id}" if group_id else str(user_id)
        
        if user_key in self.user_warnings:
            del self.user_warnings[user_key]
            self.logger.info(f"🔄 Reset warnings for user {user_key}")
            return True
        return False
        
    async def add_badword(self, word: str, category: str = "offensive",
                        severity: int = 5) -> bool:
        """
        Add word to badword list
        
        Args:
            word: Word to add
            category: Word category
            severity: Severity level (1-10)
            
        Returns:
            True if added
        """
        if not word:
            return False
            
        word_lower = word.lower()
        
        if word_lower in self.badwords:
            return False
            
        self.badwords.add(word_lower)
        
        # Update category
        self.word_categories[word_lower] = {
            "category": category,
            "severity": min(max(severity, 1), 10)
        }
        
        # Update patterns
        pattern = self._word_to_pattern(word_lower)
        self.badword_patterns.append((pattern, word_lower))
        
        self.logger.info(f"🚫 Added badword: {word_lower} ({category})")
        return True
        
    async def remove_badword(self, word: str) -> bool:
        """
        Remove word from badword list
        
        Args:
            word: Word to remove
            
        Returns:
            True if removed
        """
        word_lower = word.lower()
        
        if word_lower not in self.badwords:
            return False
            
        self.badwords.remove(word_lower)
        
        # Remove from categories
        if word_lower in self.word_categories:
            del self.word_categories[word_lower]
            
        # Remove from patterns
        self.badword_patterns = [
            (p, w) for p, w in self.badword_patterns 
            if w != word_lower
        ]
        
        self.logger.info(f"✅ Removed badword: {word_lower}")
        return True
        
    async def add_whitelist_word(self, word: str) -> bool:
        """
        Add word to whitelist
        
        Args:
            word: Word to whitelist
            
        Returns:
            True if added
        """
        if not word:
            return False
            
        word_lower = word.lower()
        self.whitelist_words.add(word_lower)
        
        self.logger.info(f"✅ Whitelisted word: {word_lower}")
        return True
        
    async def remove_whitelist_word(self, word: str) -> bool:
        """
        Remove word from whitelist
        
        Args:
            word: Word to remove
            
        Returns:
            True if removed
        """
        word_lower = word.lower()
        
        if word_lower in self.whitelist_words:
            self.whitelist_words.remove(word_lower)
            self.logger.info(f"🗑️ Removed word from whitelist: {word_lower}")
            return True
        return False
        
    async def censor_message(self, message: str,
                           matches: List[BadwordMatch]) -> str:
        """
        Censor message by replacing badwords
        
        Args:
            message: Original message
            matches: Badword matches
            
        Returns:
            Censored message
        """
        if not matches:
            return message
            
        # Sort matches by position (from end to start)
        sorted_matches = sorted(matches, key=lambda m: m.position[0], reverse=True)
        
        censored = message
        replace_with = self.config["replace_with"]
        
        for match in sorted_matches:
            start, end = match.position
            censored = censored[:start] + replace_with + censored[end:]
            
        return censored
        
    async def get_filter_stats(self) -> Dict[str, Any]:
        """Get filter statistics"""
        return {
            "total_badwords": len(self.badwords),
            "total_patterns": len(self.badword_patterns),
            "whitelist_words": len(self.whitelist_words),
            "users_with_warnings": len(self.user_warnings),
            "total_warnings": sum(data["count"] for data in self.user_warnings.values()),
            "categories": self.config["categories"],
            "config": self.config
        }
        
    async def export_word_lists(self) -> Dict[str, Any]:
        """Export word lists"""
        return {
            "badwords": sorted(list(self.badwords)),
            "whitelist": sorted(list(self.whitelist_words)),
            "categories": self.word_categories,
            "config": self.config
        }
        
    async def import_word_lists(self, data: Dict[str, Any]) -> bool:
        """
        Import word lists
        
        Args:
            data: Word lists to import
            
        Returns:
            True if successful
        """
        try:
            if "badwords" in data:
                self.badwords.update(data["badwords"])
                
            if "whitelist" in data:
                self.whitelist_words.update(data["whitelist"])
                
            if "categories" in data:
                self.word_categories.update(data["categories"])
                
            # Recreate patterns
            self._create_patterns()
            
            self.logger.info("📥 Imported word lists")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error importing word lists: {e}")
            return False
            
    async def test_filter(self, text: str) -> Dict[str, Any]:
        """
        Test filter on text
        
        Args:
            text: Text to test
            
        Returns:
            Test results
        """
        matches = await self.check_message(text, 0)
        
        censored = await self.censor_message(text, matches)
        
        return {
            "original": text,
            "matches_found": len(matches),
            "matches": [
                {
                    "word": m.word,
                    "severity": m.severity,
                    "action": m.action.value,
                    "category": m.category,
                    "position": m.position
                }
                for m in matches
            ],
            "censored": censored,
            "would_be_censored": len(matches) > 0
        }