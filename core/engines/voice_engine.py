"""
Voice Engine - Handles voice generation and processing
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
from datetime import datetime
import tempfile

from gtts import gTTS
import speech_recognition as sr

class VoiceEngine:
    """Engine for voice generation and recognition"""
    
    def __init__(self, json_loader):
        self.logger = logging.getLogger("nomi_voice")
        self.json_loader = json_loader
        self.voice_cache = {}
        self.supported_languages = {
            "bn": "বাংলা",
            "en": "English",
            "hi": "हिन्दी",
            "ar": "العربية"
        }
        self.voice_types = {
            "soft": {"speed": 0.9, "pitch": 0.8},
            "normal": {"speed": 1.0, "pitch": 1.0},
            "fast": {"speed": 1.2, "pitch": 1.1},
            "slow": {"speed": 0.7, "pitch": 0.9}
        }
        
    async def generate_voice(self, text: str, language: str = "bn", 
                           voice_type: str = "soft", speed: float = 1.0,
                           emotion: str = "neutral") -> Optional[str]:
        """
        Generate voice from text
        
        Args:
            text: Text to convert to speech
            language: Language code
            voice_type: Type of voice
            speed: Speech speed
            emotion: Emotional tone
            
        Returns:
            Path to voice file or None
        """
        if not text:
            return None
            
        # Create cache key
        cache_key = f"{hash(text)}_{language}_{voice_type}_{speed}_{emotion}"
        
        # Check cache
        if cache_key in self.voice_cache:
            cached_file = self.voice_cache[cache_key]
            if os.path.exists(cached_file):
                self.logger.debug(f"🎵 Using cached voice: {cache_key}")
                return cached_file
                
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_{timestamp}_{hash(text) % 10000}.mp3"
            filepath = Path("data/cache/voice") / filename
            
            # Create directory
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate voice using gTTS
            tts = gTTS(
                text=text,
                lang=language,
                slow=(speed < 0.8)
            )
            
            # Save to file
            tts.save(str(filepath))
            
            # Apply voice type adjustments if needed
            if voice_type != "normal":
                await self._adjust_voice(filepath, voice_type)
                
            # Apply emotion if needed
            if emotion != "neutral":
                await self._apply_emotion(filepath, emotion)
                
            # Cache the file
            self.voice_cache[cache_key] = str(filepath)
            
            # Cleanup old cache
            self._cleanup_voice_cache()
            
            self.logger.info(f"🎵 Generated voice: {len(text)} chars -> {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating voice: {e}")
            return None
            
    async def _adjust_voice(self, filepath: Path, voice_type: str):
        """Adjust voice characteristics"""
        # This is a placeholder for voice adjustment
        # In production, you might use pydub or other libraries
        pass
        
    async def _apply_emotion(self, filepath: Path, emotion: str):
        """Apply emotional tone to voice"""
        # Placeholder for emotion application
        pass
        
    async def speech_to_text(self, audio_file: BinaryIO, language: str = "bn") -> Optional[str]:
        """
        Convert speech to text
        
        Args:
            audio_file: Audio file object
            language: Language code
            
        Returns:
            Recognized text or None
        """
        try:
            recognizer = sr.Recognizer()
            
            # Load audio file
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                
            # Recognize using Google Speech Recognition
            text = recognizer.recognize_google(audio, language=language)
            
            self.logger.info(f"📝 Speech to text: {len(text)} chars recognized")
            return text
            
        except sr.UnknownValueError:
            self.logger.warning("⚠️ Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"❌ Speech recognition error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error in speech to text: {e}")
            return None
            
    async def generate_welcome_voice(self, user_data: Dict, group_data: Dict) -> Optional[str]:
        """Generate welcome voice message"""
        try:
            # Load welcome template
            config = await self.json_loader.load("responses/welcome.json")
            templates = config.get("voice_templates", [])
            
            if not templates:
                templates = [
                    "স্বাগতম {user_name}! {group_name} গ্রুপে আপনাকে স্বাগতম।"
                    "আমার নাম নোমি, আমি এই গ্রুপের সহায়ক বট।"
                ]
                
            import random
            template = random.choice(templates)
            
            # Prepare variables
            variables = {
                "user_name": user_data.get("first_name", "অতিথি"),
                "group_name": group_data.get("title", "গ্রুপ"),
                "bot_name": "নোমি"
            }
            
            # Replace variables
            text = template
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                text = text.replace(placeholder, str(value))
                
            # Generate voice
            voice_path = await self.generate_voice(
                text=text,
                language="bn",
                voice_type="soft",
                speed=0.9,
                emotion="happy"
            )
            
            return voice_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating welcome voice: {e}")
            return None
            
    async def generate_goodbye_voice(self, user_data: Dict, group_data: Dict) -> Optional[str]:
        """Generate goodbye voice message"""
        try:
            # Load goodbye template
            config = await self.json_loader.load("responses/goodbye.json")
            templates = config.get("voice_templates", [])
            
            if not templates:
                templates = [
                    "বিদায় {user_name}! {group_name} পরিবার আপনাকে স্মরণ রাখবে।"
                    "ভবিষ্যতে আবার দেখা হবে আশা করি।"
                ]
                
            import random
            template = random.choice(templates)
            
            # Prepare variables
            variables = {
                "user_name": user_data.get("first_name", "সদস্য"),
                "group_name": group_data.get("title", "গ্রুপ")
            }
            
            # Replace variables
            text = template
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                text = text.replace(placeholder, str(value))
                
            # Generate voice
            voice_path = await self.generate_voice(
                text=text,
                language="bn",
                voice_type="soft",
                speed=0.8,
                emotion="sad"
            )
            
            return voice_path
            
        except Exception as e:
            self.logger.error(f"❌ Error generating goodbye voice: {e}")
            return None
            
    def _cleanup_voice_cache(self, max_files: int = 100):
        """Cleanup old voice files from cache"""
        cache_dir = Path("data/cache/voice")
        if not cache_dir.exists():
            return
            
        # Get all voice files sorted by modification time
        voice_files = sorted(cache_dir.glob("*.mp3"), 
                           key=lambda x: x.stat().st_mtime, 
                           reverse=True)
                           
        # Remove old files
        if len(voice_files) > max_files:
            files_to_remove = voice_files[max_files:]
            for file in files_to_remove:
                try:
                    file.unlink()
                    # Remove from cache dict
                    keys_to_remove = [k for k, v in self.voice_cache.items() 
                                     if v == str(file)]
                    for key in keys_to_remove:
                        del self.voice_cache[key]
                except:
                    pass
                    
            self.logger.info(f"🧹 Cleaned up {len(files_to_remove)} old voice files")
            
    async def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice engine statistics"""
        cache_dir = Path("data/cache/voice")
        total_files = len(list(cache_dir.glob("*.mp3"))) if cache_dir.exists() else 0
        
        return {
            "cache_size": len(self.voice_cache),
            "total_voice_files": total_files,
            "supported_languages": len(self.supported_languages),
            "voice_types": list(self.voice_types.keys())
        }
        
    async def set_language(self, language: str):
        """
        Set default language for voice generation
        
        Args:
            language: Language code
        """
        if language in self.supported_languages:
            # Save to config
            config = await self.json_loader.load("responses/voice_reply.json")
            config["default_language"] = language
            await self.json_loader.save("responses/voice_reply.json", config)
            
            self.logger.info(f"🌍 Set default language to: {language}")
        else:
            self.logger.warning(f"⚠️ Unsupported language: {language}")
            
    async def list_available_voices(self) -> Dict[str, Any]:
        """List available voice configurations"""
        return {
            "languages": self.supported_languages,
            "voice_types": self.voice_types,
            "emotions": ["neutral", "happy", "sad", "excited", "calm"],
            "current_settings": {
                "default_language": "bn",
                "default_voice_type": "soft",
                "cache_enabled": True
            }
        }