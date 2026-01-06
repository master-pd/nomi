"""
String Utilities - String manipulation and processing
"""

import re
import random
import string
from typing import List, Dict, Any, Optional, Tuple
import unicodedata
from difflib import SequenceMatcher

class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def normalize_bangla_text(text: str) -> str:
        """Normalize Bangla text for consistent processing"""
        if not text:
            return ""
            
        # Normalize Unicode
        text = unicodedata.normalize('NFC', text)
        
        # Replace common variations
        replacements = {
            'য়': 'য়',  # Yaphala
            'ড়': 'ড়',  # Raphala
            'ঢ়': 'ঢ়',  # Rhaphala
            '্‌': '',   # Zero width joiner
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    @staticmethod
    def contains_bangla(text: str) -> bool:
        """Check if text contains Bangla characters"""
        bangla_range = range(0x0980, 0x09FF + 1)
        return any(ord(char) in bangla_range for char in text)
        
    @staticmethod
    def get_bangla_percentage(text: str) -> float:
        """Calculate percentage of Bangla characters in text"""
        if not text:
            return 0.0
            
        bangla_range = range(0x0980, 0x09FF + 1)
        total_chars = len(text)
        bangla_chars = sum(1 for char in text if ord(char) in bangla_range)
        
        return (bangla_chars / total_chars) * 100 if total_chars > 0 else 0.0
        
    @staticmethod
    def transliterate_bangla_to_english(text: str) -> str:
        """Transliterate Bangla text to English (Romanization)"""
        # Basic transliteration mapping
        mapping = {
            'অ': 'o', 'আ': 'a', 'ই': 'i', 'ঈ': 'ee', 'উ': 'u', 'ঊ': 'oo',
            'ঋ': 'ri', 'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou',
            'ক': 'k', 'খ': 'kh', 'গ': 'g', 'ঘ': 'gh', 'ঙ': 'ng',
            'চ': 'ch', 'ছ': 'chh', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'n',
            'ট': 't', 'ঠ': 'th', 'ড': 'd', 'ঢ': 'dh', 'ণ': 'n',
            'ত': 't', 'থ': 'th', 'দ': 'd', 'ধ': 'dh', 'ন': 'n',
            'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh', 'ম': 'm',
            'য': 'j', 'র': 'r', 'ল': 'l', 'শ': 'sh', 'ষ': 'sh', 'স': 's',
            'হ': 'h', 'ড়': 'r', 'ঢ়': 'rh', 'য়': 'y', 'ৎ': 't',
            'ং': 'ng', 'ঃ': 'h', '্': '', 'া': 'a', 'ি': 'i', 'ী': 'ee',
            'ু': 'u', 'ূ': 'oo', 'ৃ': 'ri', 'ে': 'e', 'ৈ': 'oi',
            'ো': 'o', 'ৌ': 'ou', '্‌': '', 'ঁ': 'n'
        }
        
        result = []
        for char in text:
            result.append(mapping.get(char, char))
            
        return ''.join(result)
        
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract hashtags from text"""
        hashtag_pattern = r'#(\w+)'
        return re.findall(hashtag_pattern, text)
        
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract mentions from text"""
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, text)
        
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://\S+'
        return re.findall(url_pattern, text)
        
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags from text"""
        html_pattern = r'<[^>]+>'
        return re.sub(html_pattern, '', text)
        
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, 
                     suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
            
        return text[:max_length - len(suffix)] + suffix
        
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Basic sentence splitting for Bangla and English
        sentence_endings = r'[।!?\.]\s+'
        sentences = re.split(sentence_endings, text)
        
        # Remove empty strings
        return [s.strip() for s in sentences if s.strip()]
        
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
            
        # Split by whitespace and filter empty strings
        words = [word for word in text.split() if word.strip()]
        return len(words)
        
    @staticmethod
    def count_characters(text: str, count_spaces: bool = True) -> int:
        """Count characters in text"""
        if not text:
            return 0
            
        if not count_spaces:
            text = text.replace(' ', '').replace('\t', '').replace('\n', '')
            
        return len(text)
        
    @staticmethod
    def get_word_frequency(text: str) -> Dict[str, int]:
        """Get word frequency from text"""
        words = text.lower().split()
        frequency = {}
        
        for word in words:
            # Remove punctuation
            word = word.strip(string.punctuation + '।')
            if word:
                frequency[word] = frequency.get(word, 0) + 1
                
        return frequency
        
    @staticmethod
    def find_longest_word(text: str) -> str:
        """Find longest word in text"""
        words = text.split()
        if not words:
            return ""
            
        return max(words, key=len)
        
    @staticmethod
    def find_most_common_word(text: str) -> Tuple[str, int]:
        """Find most common word in text"""
        frequency = StringUtils.get_word_frequency(text)
        if not frequency:
            return ("", 0)
            
        most_common = max(frequency.items(), key=lambda x: x[1])
        return most_common
        
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0 to 1)"""
        return SequenceMatcher(None, text1, text2).ratio()
        
    @staticmethod
    def generate_random_string(length: int = 8,
                             include_digits: bool = True,
                             include_special: bool = False) -> str:
        """Generate random string"""
        characters = string.ascii_letters
        
        if include_digits:
            characters += string.digits
            
        if include_special:
            characters += "!@#$%^&*()_+-="
            
        return ''.join(random.choice(characters) for _ in range(length))
        
    @staticmethod
    def generate_bangla_string(length: int = 8) -> str:
        """Generate random Bangla string"""
        bangla_chars = [
            'অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'এ', 'ঐ', 'ও', 'ঔ',
            'ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ',
            'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন',
            'প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'শ', 'ষ', 'স', 'হ',
            'া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ'
        ]
        
        return ''.join(random.choice(bangla_chars) for _ in range(length))
        
    @staticmethod
    def camel_to_snake(text: str) -> str:
        """Convert camelCase to snake_case"""
        # Insert underscore before uppercase letters
        result = []
        for i, char in enumerate(text):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
            
        return ''.join(result)
        
    @staticmethod
    def snake_to_camel(text: str) -> str:
        """Convert snake_case to camelCase"""
        words = text.split('_')
        return words[0] + ''.join(word.capitalize() for word in words[1:])
        
    @staticmethod
    def encode_base64(text: str) -> str:
        """Encode text to base64"""
        import base64
        return base64.b64encode(text.encode()).decode()
        
    @staticmethod
    def decode_base64(encoded: str) -> str:
        """Decode base64 to text"""
        import base64
        return base64.b64decode(encoded).decode()
        
    @staticmethod
    def obfuscate_email(email: str) -> str:
        """Obfuscate email address"""
        if '@' not in email:
            return email
            
        username, domain = email.split('@')
        
        if len(username) <= 2:
            obfuscated_user = username[0] + '*' * (len(username) - 1)
        else:
            obfuscated_user = username[0] + '*' * (len(username) - 2) + username[-1]
            
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            obfuscated_domain = domain_parts[0][0] + '*' * (len(domain_parts[0]) - 1) + \
                               '.' + '.'.join(domain_parts[1:])
        else:
            obfuscated_domain = domain
            
        return f"{obfuscated_user}@{obfuscated_domain}"
        
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)
        
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text (Bangladeshi format)"""
        # Bangladeshi phone number patterns
        patterns = [
            r'\+8801[3-9]\d{8}',  # +8801XXXXXXXXX
            r'01[3-9]\d{8}',       # 01XXXXXXXXX
            r'1[3-9]\d{8}'         # 1XXXXXXXXX
        ]
        
        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))
            
        return numbers
        
    @staticmethod
    def create_slug(text: str) -> str:
        """Create URL slug from text"""
        # Convert to lowercase
        text = text.lower()
        
        # Replace non-alphanumeric with hyphens
        text = re.sub(r'[^a-z0-9\u0980-\u09FF]+', '-', text)
        
        # Remove leading/trailing hyphens
        text = text.strip('-')
        
        # Remove multiple consecutive hyphens
        text = re.sub(r'-+', '-', text)
        
        return text
        
    @staticmethod
    def is_palindrome(text: str) -> bool:
        """Check if text is palindrome"""
        # Remove spaces and convert to lowercase
        clean_text = re.sub(r'\s+', '', text.lower())
        return clean_text == clean_text[::-1]
        
    @staticmethod
    def reverse_words(text: str) -> str:
        """Reverse words in text"""
        words = text.split()
        return ' '.join(reversed(words))
        
    @staticmethod
    def capitalize_sentences(text: str) -> str:
        """Capitalize first letter of each sentence"""
        sentences = StringUtils.split_into_sentences(text)
        capitalized = []
        
        for sentence in sentences:
            if sentence:
                capitalized.append(sentence[0].upper() + sentence[1:])
            else:
                capitalized.append("")
                
        # Join with period and space
        return '. '.join(capitalized)
        
    @staticmethod
    def remove_duplicate_lines(text: str) -> str:
        """Remove duplicate lines from text"""
        lines = text.split('\n')
        unique_lines = []
        seen = set()
        
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
                
        return '\n'.join(unique_lines)