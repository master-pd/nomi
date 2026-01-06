"""
Time Utilities - Date and time related functions
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pytz
from dateutil.relativedelta import relativedelta

class TimeUtils:
    """Time and date utility functions"""
    
    @staticmethod
    def get_current_time(timezone: str = "Asia/Dhaka") -> datetime:
        """Get current time in specified timezone"""
        tz = pytz.timezone(timezone)
        return datetime.now(tz)
        
    @staticmethod
    def format_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string"""
        return dt.strftime(format_str)
        
    @staticmethod
    def parse_time(time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse string to datetime"""
        try:
            return datetime.strptime(time_str, format_str)
        except:
            return None
            
    @staticmethod
    def get_time_ago(dt: datetime) -> str:
        """Get human-readable time ago string"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} বছর আগে"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} মাস আগে"
        elif diff.days > 0:
            return f"{diff.days} দিন আগে"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ঘন্টা আগে"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} মিনিট আগে"
        else:
            return "অল্পক্ষণ আগে"
            
    @staticmethod
    def get_bangla_time(dt: Optional[datetime] = None) -> str:
        """Get time in Bengali format"""
        if dt is None:
            dt = datetime.now()
            
        # Bengali month names
        bangla_months = [
            "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
            "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"
        ]
        
        # Bengali day names
        bangla_days = [
            "রবিবার", "সোমবার", "মঙ্গলবার", "বুধবার",
            "বৃহস্পতিবার", "শুক্রবার", "শনিবার"
        ]
        
        month_name = bangla_months[dt.month - 1]
        day_name = bangla_days[dt.weekday()]
        
        # Bengali numerals
        bangla_numerals = {
            '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
            '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'
        }
        
        def to_bangla_num(num_str: str) -> str:
            return ''.join(bangla_numerals.get(d, d) for d in str(num_str))
            
        date_str = f"{to_bangla_num(dt.day)} {month_name} {to_bangla_num(dt.year)}"
        time_str = f"{to_bangla_num(dt.hour)}:{to_bangla_num(dt.minute)}:{to_bangla_num(dt.second)}"
        
        return f"{day_name}, {date_str}, {time_str}"
        
    @staticmethod
    def get_account_age(join_date: datetime) -> Dict[str, Any]:
        """Calculate account age"""
        now = datetime.now()
        delta = relativedelta(now, join_date)
        
        return {
            "years": delta.years,
            "months": delta.months,
            "days": delta.days,
            "hours": delta.hours,
            "minutes": delta.minutes,
            "total_days": (now - join_date).days
        }
        
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to human readable"""
        if seconds < 60:
            return f"{seconds} সেকেন্ড"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} মিনিট"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ঘন্টা {minutes} মিনিট"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} দিন {hours} ঘন্টা"
            
    @staticmethod
    def is_weekend(dt: Optional[datetime] = None) -> bool:
        """Check if date is weekend"""
        if dt is None:
            dt = datetime.now()
        return dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday
        
    @staticmethod
    def is_holiday(dt: Optional[datetime] = None) -> bool:
        """Check if date is holiday in Bangladesh"""
        if dt is None:
            dt = datetime.now()
            
        # Major Bangladeshi holidays (simplified)
        holidays = {
            (1, 1): "নববর্ষ",
            (2, 21): "শহীদ দিবস",
            (3, 17): "জাতির পিতার জন্মদিন",
            (3, 26): "স্বাধীনতা দিবস",
            (4, 14): "বাংলা নববর্ষ",
            (5, 1): "মে দিবস",
            (8, 15): "জাতীয় শোক দিবস",
            (12, 16): "বিজয় দিবস"
        }
        
        return (dt.month, dt.day) in holidays
        
    @staticmethod
    def get_next_reminder_time(base_time: datetime, 
                             interval: str = "1d") -> datetime:
        """Get next reminder time based on interval"""
        intervals = {
            "1h": timedelta(hours=1),
            "3h": timedelta(hours=3),
            "6h": timedelta(hours=6),
            "12h": timedelta(hours=12),
            "1d": timedelta(days=1),
            "3d": timedelta(days=3),
            "1w": timedelta(weeks=1),
            "2w": timedelta(weeks=2),
            "1m": timedelta(days=30)
        }
        
        delta = intervals.get(interval, timedelta(days=1))
        return base_time + delta
        
    @staticmethod
    def calculate_time_difference(start: datetime, end: datetime) -> Dict[str, int]:
        """Calculate difference between two datetimes"""
        diff = end - start
        
        return {
            "total_seconds": int(diff.total_seconds()),
            "days": diff.days,
            "hours": diff.seconds // 3600,
            "minutes": (diff.seconds % 3600) // 60,
            "seconds": diff.seconds % 60
        }
        
    @staticmethod
    def get_season(dt: Optional[datetime] = None) -> str:
        """Get current season in Bangladesh"""
        if dt is None:
            dt = datetime.now()
            
        month = dt.month
        
        if month in [12, 1, 2]:
            return "শীত"
        elif month in [3, 4, 5]:
            return "গ্রীষ্ম"
        elif month in [6, 7, 8, 9]:
            return "বর্ষা"
        else:
            return "শরৎ"
            
    @staticmethod
    def is_rush_hour(dt: Optional[datetime] = None) -> bool:
        """Check if current time is rush hour"""
        if dt is None:
            dt = datetime.now()
            
        hour = dt.hour
        # Bangladesh rush hours: 8-10 AM and 5-7 PM
        return (8 <= hour < 10) or (17 <= hour < 19)
        
    @staticmethod
    def format_relative_time(dt: datetime) -> str:
        """Format relative time (today, yesterday, etc.)"""
        now = datetime.now()
        today = now.date()
        input_date = dt.date()
        
        if input_date == today:
            return "আজ"
        elif input_date == today - timedelta(days=1):
            return "গতকাল"
        elif input_date == today + timedelta(days=1):
            return "আগামীকাল"
        else:
            diff_days = (input_date - today).days
            if diff_days > 0:
                return f"{diff_days} দিন পর"
            else:
                return f"{abs(diff_days)} দিন আগে"
                
    @staticmethod
    def get_time_of_day(dt: Optional[datetime] = None) -> str:
        """Get time of day (morning, afternoon, etc.)"""
        if dt is None:
            dt = datetime.now()
            
        hour = dt.hour
        
        if 5 <= hour < 12:
            return "সকাল"
        elif 12 <= hour < 15:
            return "দুপুর"
        elif 15 <= hour < 18:
            return "বিকাল"
        elif 18 <= hour < 21:
            return "সন্ধ্যা"
        else:
            return "রাত"