"""
Random Utilities - Random data generation
"""

import random
import string
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class RandomUtils:
    """Random data generation utilities"""
    
    @staticmethod
    def random_string(length: int = 10, 
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
    def random_bangla_string(length: int = 10) -> str:
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
    def random_number(min_val: int = 0, 
                     max_val: int = 100) -> int:
        """Generate random number"""
        return random.randint(min_val, max_val)
        
    @staticmethod
    def random_float(min_val: float = 0.0,
                    max_val: float = 1.0,
                    decimal_places: int = 2) -> float:
        """Generate random float"""
        value = random.uniform(min_val, max_val)
        return round(value, decimal_places)
        
    @staticmethod
    def random_boolean() -> bool:
        """Generate random boolean"""
        return random.choice([True, False])
        
    @staticmethod
    def random_date(start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> datetime:
        """Generate random date"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
            
        if end_date is None:
            end_date = datetime.now()
            
        time_between = end_date - start_date
            days_between = time_between.days
        random_days = random.randrange(days_between)
        
        return start_date + timedelta(days=random_days)
        
    @staticmethod
    def random_time() -> str:
        """Generate random time"""
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return f"{hour:02d}:{minute:02d}:{second:02d}"
        
    @staticmethod
    def random_color() -> str:
        """Generate random hex color"""
        return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
    @staticmethod
    def random_choice(choices: List[Any]) -> Any:
        """Random choice from list"""
        return random.choice(choices)
        
    @staticmethod
    def random_sample(choices: List[Any], 
                     sample_size: int) -> List[Any]:
        """Random sample from list"""
        return random.sample(choices, min(sample_size, len(choices)))
        
    @staticmethod
    def shuffle_list(items: List[Any]) -> List[Any]:
        """Shuffle list"""
        shuffled = items.copy()
        random.shuffle(shuffled)
        return shuffled
        
    @staticmethod
    def random_name() -> str:
        """Generate random name"""
        first_names = [
            "আহমেদ", "করিম", "রহিম", "সুমন", "রানা",
            "সাকিব", "তামিম", "মুশফিক", "মাশরাফি", "মাহমুদ",
            "ফারহান", "জুবায়ের", "সাদমান", "ইমরান", "নাঈম"
        ]
        
        last_names = [
            "চৌধুরী", "খান", "মিয়া", "হোসেন", "আলম",
            "রহমান", "সিকদার", "মোল্লা", "শেখ", "বেগম"
        ]
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"
        
    @staticmethod
    def random_bangla_sentence(word_count: int = 10) -> str:
        """Generate random Bangla sentence"""
        words = [
            "আমি", "তুমি", "সে", "আমরা", "তোমরা", "তারা",
            "খাওয়া", "পড়া", "দেখা", "শোনা", "যাওয়া", "আসা",
            "বই", "কলম", "টেবিল", "চেয়ার", "ঘর", "বাড়ি",
            "সুন্দর", "ভালো", "মন্দ", "বড়", "ছোট", "নতুন",
            "আজ", "কাল", "পরশু", "সকাল", "দুপুর", "বিকাল"
        ]
        
        sentence_words = random.sample(words, min(word_count, len(words)))
        return ' '.join(sentence_words) + '।'
        
    @staticmethod
    def random_user_agent() -> str:
        """Generate random user agent"""
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        ]
        
        return random.choice(browsers)
        
    @staticmethod
    def random_ip_address() -> str:
        """Generate random IP address"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
        
    @staticmethod
    def random_email() -> str:
        """Generate random email"""
        domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
        username = RandomUtils.random_string(8, include_digits=True)
        domain = random.choice(domains)
        
        return f"{username}@{domain}"
        
    @staticmethod
    def random_phone() -> str:
        """Generate random Bangladeshi phone number"""
        prefixes = ["13", "14", "15", "16", "17", "18", "19"]
        prefix = random.choice(prefixes)
        number = ''.join(str(random.randint(0, 9)) for _ in range(8))
        
        return f"01{prefix}{number}"
        
    @staticmethod
    def random_address() -> str:
        """Generate random address"""
        streets = ["রাস্তা", "সড়ক", "লেন", "গলি"]
        areas = ["ধানমন্ডি", "গুলশান", "বনানী", "মোহাম্মদপুর", "মতিঝিল"]
        cities = ["ঢাকা", "চট্টগ্রাম", "সিলেট", "রাজশাহী", "খুলনা"]
        
        street_no = random.randint(1, 100)
        street_name = RandomUtils.random_bangla_string(5)
        street_type = random.choice(streets)
        area = random.choice(areas)
        city = random.choice(cities)
        
        return f"{street_no} নং {street_name}{street_type}, {area}, {city}"