"""
Bangla Voice Generation System
Using gTTS and custom TTS engines
"""

import os
import logging
from typing import Optional, Union
from gtts import gTTS
import tempfile
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class VoiceUtils:
    """Professional Bangla voice generation utilities"""
    
    def __init__(self):
        self.temp_dir = Config.TEMP_VOICE
        self.lang = Config.VOICE_LANG  # 'bn' for Bangla
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Voice settings
        self.voice_settings = {
            'welcome': {
                'slow': False,
                'lang': 'bn',
                'tld': 'com.bd'  # Bangladesh domain for better accent
            },
            'goodbye': {
                'slow': True,  # Slower for goodbye
                'lang': 'bn',
                'tld': 'com.bd'
            },
            'reply': {
                'slow': False,
                'lang': 'bn',
                'tld': 'com'
            },
            'announcement': {
                'slow': False,
                'lang': 'bn',
                'tld': 'com.bd'
            }
        }
    
    def text_to_speech(self, text: str, voice_type: str = 'reply') -> Optional[str]:
        """
        Convert text to Bangla speech
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text for TTS")
                return None
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Get voice settings
            settings = self.voice_settings.get(voice_type, self.voice_settings['reply'])
            
            # Generate speech using gTTS
            tts = gTTS(
                text=cleaned_text,
                lang=settings['lang'],
                slow=settings['slow'],
                tld=settings.get('tld', 'com')
            )
            
            # Save to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{voice_type}_{timestamp}.mp3"
            filepath = os.path.join(self.temp_dir, filename)
            
            tts.save(filepath)
            
            logger.info(f"Generated voice file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None
    
    def generate_welcome_voice(self, user_name: str, group_name: str) -> Optional[str]:
        """
        Generate welcome voice message
        """
        try:
            # Bangla welcome message
            welcome_text = f"""
            আসসালামু আলাইকুম {user_name}।
            
            {group_name} গ্রুপে আপনাকে স্বাগতম।
            
            গ্রুপের নিয়ম মেনে চলুন এবং উপভোগ করুন।
            
            ধন্যবাদ।
            """
            
            return self.text_to_speech(welcome_text, 'welcome')
            
        except Exception as e:
            logger.error(f"Error generating welcome voice: {e}")
            return None
    
    def generate_goodbye_voice(self, user_name: str) -> Optional[str]:
        """
        Generate goodbye voice message
        """
        try:
            # Bangla goodbye message
            goodbye_text = f"""
            আল্লাহ হাফেজ {user_name}।
            
            আমাদের সাথে থাকার জন্য ধন্যবাদ।
            
            আপনার জন্য শুভকামনা রইল।
            
            আবার দেখা হবে ইনশাআল্লাহ।
            """
            
            return self.text_to_speech(goodbye_text, 'goodbye')
            
        except Exception as e:
            logger.error(f"Error generating goodbye voice: {e}")
            return None
    
    def generate_auto_reply_voice(self, reply_text: str) -> Optional[str]:
        """
        Generate auto reply voice message
        """
        try:
            return self.text_to_speech(reply_text, 'reply')
        except Exception as e:
            logger.error(f"Error generating auto reply voice: {e}")
            return None
    
    def generate_announcement_voice(self, announcement: str) -> Optional[str]:
        """
        Generate announcement voice message
        """
        try:
            # Add announcement prefix
            full_text = f"গুরুত্বপূর্ণ ঘোষণা: {announcement}"
            return self.text_to_speech(full_text, 'announcement')
        except Exception as e:
            logger.error(f"Error generating announcement voice: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for better TTS output
        """
        try:
            # Remove markdown
            import re
            
            # Remove markdown bold
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'__(.*?)__', r'\1', text)
            
            # Remove markdown italic
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = re.sub(r'_(.*?)_', r'\1', text)
            
            # Remove markdown code
            text = re.sub(r'`(.*?)`', r'\1', text)
            
            # Remove URLs
            text = re.sub(r'http[s]?://\S+', '', text)
            
            # Remove mentions
            text = re.sub(r'@\w+', '', text)
            
            # Remove excessive whitespace
            text = ' '.join(text.split())
            
            # Replace common abbreviations
            replacements = {
                'ভাই': 'ভাইয়া',
                'আপু': 'আপু',
                'bro': 'ভাই',
                'sis': 'আপু',
                'plz': 'প্লিজ',
                'pls': 'প্লিজ',
                'thx': 'থ্যাংক্স',
                'tnx': 'থ্যাংক্স',
                'ty': 'থ্যাংক ইউ',
                'wlc': 'ওয়েলকাম',
                'wlcm': 'ওয়েলকাম',
                'ok': 'ওকে',
                'okay': 'ওকে',
                'gm': 'গুড মর্নিং',
                'gn': 'গুড নাইট',
                'btw': 'বাই দ্য ওয়ে',
                'lol': 'লল',
                'rofl': 'রফল',
                'omg': 'ওহ মাই গড',
                'wtf': 'হোয়াট দ্য ফাক',
                'brb': 'বি রাইট ব্যাক',
                'ttyl': 'টক টু ইউ লেটার',
                'idk': 'আই ডোন্ট নো',
                'imo': 'ইন মাই অপিনিয়ন',
                'fyi': 'ফর ইয়োর ইনফরমেশন',
                'asap': 'এজ সুন এজ পসিবল',
                'DIY': 'ডু ইট ইয়োরসেলফ',
                'FAQ': 'ফ্রিকোয়েন্টলি আস্কড কোয়েশ্চনস',
                'CEO': 'চিফ এক্সিকিউটিভ অফিসার',
                'COVID': 'কোভিড',
                'AI': 'আর্টিফিশিয়াল ইন্টেলিজেন্স',
                'UI': 'ইউজার ইন্টারফেস',
                'UX': 'ইউজার এক্সপেরিয়েন্স'
            }
            
            for abbr, full in replacements.items():
                text = text.replace(abbr, full)
                text = text.replace(abbr.upper(), full)
                text = text.replace(abbr.lower(), full)
                text = text.replace(abbr.capitalize(), full)
            
            # Ensure proper Bangla punctuation
            text = text.replace('?', '? ')
            text = text.replace('!', '! ')
            text = text.replace(',', ', ')
            text = text.replace('.', '. ')
            
            # Remove multiple spaces
            text = ' '.join(text.split())
            
            # Limit length for TTS (gTTS has limits)
            if len(text) > 500:
                text = text[:497] + "..."
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning text for TTS: {e}")
            return text
    
    def get_voice_duration(self, filepath: str) -> float:
        """
        Get duration of voice file in seconds
        """
        try:
            import mutagen.mp3
            
            audio = mutagen.mp3.MP3(filepath)
            return audio.info.length
        except Exception as e:
            logger.error(f"Error getting voice duration: {e}")
            return 0.0
    
    def merge_voice_files(self, filepaths: list, output_filename: str = None) -> Optional[str]:
        """
        Merge multiple voice files into one
        """
        try:
            if not filepaths:
                return None
            
            if len(filepaths) == 1:
                return filepaths[0]
            
            from pydub import AudioSegment
            
            # Load first file
            combined = AudioSegment.from_file(filepaths[0])
            
            # Append other files
            for filepath in filepaths[1:]:
                audio = AudioSegment.from_file(filepath)
                combined = combined + AudioSegment.silent(duration=500) + audio  # 500ms silence between
            
            # Save merged file
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"merged_{timestamp}.mp3"
            
            output_path = os.path.join(self.temp_dir, output_filename)
            combined.export(output_path, format="mp3")
            
            logger.info(f"Merged {len(filepaths)} voice files to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging voice files: {e}")
            # Fallback: return first file
            return filepaths[0] if filepaths else None
    
    def add_audio_effects(self, filepath: str, effect: str = "echo") -> Optional[str]:
        """
        Add audio effects to voice file
        """
        try:
            from pydub import AudioSegment
            from pydub.effects import compress_dynamic_range, normalize
            
            # Load audio
            audio = AudioSegment.from_file(filepath)
            
            # Apply effects
            if effect == "echo":
                # Simple echo effect
                echo = audio - 10  # Quieter echo
                combined = audio.overlay(echo, position=200)  # 200ms delay
                combined = combined.overlay(echo - 5, position=400)  # Second echo
            elif effect == "radio":
                # Radio effect (bandpass filter simulation)
                combined = audio.low_pass_filter(3000).high_pass_filter(300)
            elif effect == "deep":
                # Deep voice effect
                combined = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * 0.9)
                }).set_frame_rate(audio.frame_rate)
            else:
                # Just normalize
                combined = normalize(audio)
            
            # Compress dynamic range for consistency
            combined = compress_dynamic_range(combined, threshold=-20.0, ratio=4.0)
            
            # Save with effect
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"effect_{effect}_{timestamp}.mp3"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            combined.export(output_path, format="mp3", bitrate="64k")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding audio effects: {e}")
            return filepath  # Return original if effects fail
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Cleanup temporary voice files
        """
        try:
            import time
            current_time = time.time()
            cutoff = older_than_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                if filename.endswith('.mp3'):
                    filepath = os.path.join(self.temp_dir, filename)
                    if os.path.isfile(filepath):
                        file_time = os.path.getmtime(filepath)
                        if current_time - file_time > cutoff:
                            os.remove(filepath)
                            logger.debug(f"Cleaned up voice file: {filename}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up voice files: {e}")
    
    def get_voice_statistics(self) -> Dict:
        """
        Get voice generation statistics
        """
        try:
            stats = {
                "total_files": 0,
                "total_duration": 0,
                "files_by_type": {},
                "recent_files": []
            }
            
            # Count files and calculate duration
            for filename in os.listdir(self.temp_dir):
                if filename.endswith('.mp3'):
                    stats["total_files"] += 1
                    
                    # Categorize by type
                    file_type = "unknown"
                    if filename.startswith("welcome_"):
                        file_type = "welcome"
                    elif filename.startswith("goodbye_"):
                        file_type = "goodbye"
                    elif filename.startswith("reply_"):
                        file_type = "reply"
                    elif filename.startswith("announcement_"):
                        file_type = "announcement"
                    
                    stats["files_by_type"][file_type] = stats["files_by_type"].get(file_type, 0) + 1
                    
                    # Get file info for recent files
                    filepath = os.path.join(self.temp_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    duration = self.get_voice_duration(filepath)
                    stats["total_duration"] += duration
                    
                    # Add to recent files (last 10)
                    stats["recent_files"].append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "duration": duration,
                        "created": datetime.fromtimestamp(file_time).isoformat()
                    })
            
            # Sort recent files by creation time
            stats["recent_files"].sort(key=lambda x: x["created"], reverse=True)
            stats["recent_files"] = stats["recent_files"][:10]
            
            # Convert duration to readable format
            minutes = int(stats["total_duration"] // 60)
            seconds = int(stats["total_duration"] % 60)
            stats["total_duration_formatted"] = f"{minutes}m {seconds}s"
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting voice statistics: {e}")
            return {}