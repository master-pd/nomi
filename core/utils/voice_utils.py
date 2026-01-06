"""
Voice Utilities - Voice processing and manipulation
"""

import asyncio
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import wave
import audioop
from gtts import gTTS
import speech_recognition as sr

class VoiceUtils:
    """Voice processing utilities"""
    
    @staticmethod
    async def text_to_speech(text: str,
                           language: str = "bn",
                           slow: bool = False) -> Optional[BytesIO]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            language: Language code
            slow: Whether to speak slowly
            
        Returns:
            BytesIO with audio data or None
        """
        try:
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # Save to BytesIO
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer
        except Exception as e:
            print(f"Error converting text to speech: {e}")
            return None
            
    @staticmethod
    async def speech_to_text(audio_data: BytesIO,
                           language: str = "bn-BD") -> Optional[str]:
        """
        Convert speech to text
        
        Args:
            audio_data: Audio data in BytesIO
            language: Language code
            
        Returns:
            Recognized text or None
        """
        try:
            recognizer = sr.Recognizer()
            
            # Use audio_data with AudioFile
            with sr.AudioFile(audio_data) as source:
                audio = recognizer.record(source)
                
            # Recognize using Google Speech Recognition
            text = recognizer.recognize_google(audio, language=language)
            return text
            
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results: {e}")
        except Exception as e:
            print(f"Error in speech to text: {e}")
            
        return None
        
    @staticmethod
    async def get_audio_info(audio_data: BytesIO) -> Dict[str, Any]:
        """
        Get audio file information
        
        Args:
            audio_data: Audio data in BytesIO
            
        Returns:
            Audio information dictionary
        """
        try:
            with wave.open(audio_data, 'rb') as wav_file:
                return {
                    "channels": wav_file.getnchannels(),
                    "sample_width": wav_file.getsampwidth(),
                    "frame_rate": wav_file.getframerate(),
                    "frames": wav_file.getnframes(),
                    "duration": wav_file.getnframes() / wav_file.getframerate()
                }
        except:
            # Try to estimate for non-WAV files
            audio_data.seek(0)
            content = audio_data.read()
            return {
                "size_bytes": len(content),
                "duration_estimate": len(content) / 16000  # Rough estimate
            }
            
    @staticmethod
    async def adjust_volume(audio_data: BytesIO,
                          factor: float) -> Optional[BytesIO]:
        """
        Adjust audio volume
        
        Args:
            audio_data: Audio data in BytesIO
            factor: Volume adjustment factor (0.5 = half, 2.0 = double)
            
        Returns:
            Adjusted audio data or None
        """
        try:
            # This is a simplified version
            # For production, use proper audio processing library
            audio_data.seek(0)
            audio_bytes = audio_data.read()
            
            # Simple volume adjustment (for PCM audio)
            adjusted = audioop.mul(audio_bytes, 2, factor)
            
            output = BytesIO(adjusted)
            output.seek(0)
            return output
            
        except Exception as e:
            print(f"Error adjusting volume: {e}")
            return None
            
    @staticmethod
    async def concatenate_audio(audio_files: List[BytesIO]) -> Optional[BytesIO]:
        """
        Concatenate multiple audio files
        
        Args:
            audio_files: List of audio data in BytesIO
            
        Returns:
            Concatenated audio data or None
        """
        if not audio_files:
            return None
            
        try:
            output = BytesIO()
            
            for i, audio in enumerate(audio_files):
                audio.seek(0)
                if i == 0:
                    output.write(audio.read())
                else:
                    # Simple concatenation (for same format)
                    output.write(audio.read())
                    
            output.seek(0)
            return output
            
        except Exception as e:
            print(f"Error concatenating audio: {e}")
            return None
            
    @staticmethod
    async def generate_welcome_voice(user_data: Dict[str, Any],
                                   group_data: Dict[str, Any]) -> Optional[Path]:
        """
        Generate welcome voice message
        
        Args:
            user_data: User information
            group_data: Group information
            
        Returns:
            Path to voice file or None
        """
        try:
            # Create welcome message
            user_name = user_data.get("first_name", "অতিথি")
            group_name = group_data.get("title", "গ্রুপ")
            
            message = f"স্বাগতম {user_name}! {group_name} গ্রুপে আপনাকে স্বাগতম।"
            
            # Generate speech
            audio_buffer = await VoiceUtils.text_to_speech(
                text=message,
                language="bn",
                slow=False
            )
            
            if audio_buffer:
                # Save to file
                timestamp = int(time.time())
                filename = f"welcome_voice_{user_data.get('id', 'user')}_{timestamp}.mp3"
                filepath = Path("data/cache/voice") / filename
                
                await FileUtils.ensure_directory(filepath.parent)
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(audio_buffer.read())
                    
                return filepath
                
        except Exception as e:
            print(f"Error generating welcome voice: {e}")
            
        return None
        
    @staticmethod
    async def generate_goodbye_voice(user_data: Dict[str, Any],
                                   group_data: Dict[str, Any]) -> Optional[Path]:
        """
        Generate goodbye voice message
        
        Args:
            user_data: User information
            group_data: Group information
            
        Returns:
            Path to voice file or None
        """
        try:
            user_name = user_data.get("first_name", "সদস্য")
            group_name = group_data.get("title", "গ্রুপ")
            
            message = f"বিদায় {user_name}! {group_name} পরিবার আপনাকে স্মরণ রাখবে।"
            
            audio_buffer = await VoiceUtils.text_to_speech(
                text=message,
                language="bn",
                slow=False
            )
            
            if audio_buffer:
                timestamp = int(time.time())
                filename = f"goodbye_voice_{user_data.get('id', 'user')}_{timestamp}.mp3"
                filepath = Path("data/cache/voice") / filename
                
                await FileUtils.ensure_directory(filepath.parent)
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(audio_buffer.read())
                    
                return filepath
                
        except Exception as e:
            print(f"Error generating goodbye voice: {e}")
            
        return None
        
    @staticmethod
    async def create_voice_message(text: str,
                                 voice_type: str = "default") -> Optional[Path]:
        """
        Create voice message from text
        
        Args:
            text: Text to convert
            voice_type: Type of voice (for future expansion)
            
        Returns:
            Path to voice file or None
        """
        try:
            audio_buffer = await VoiceUtils.text_to_speech(
                text=text,
                language="bn",
                slow=False
            )
            
            if audio_buffer:
                timestamp = int(time.time())
                filename = f"voice_message_{hash(text) % 10000}_{timestamp}.mp3"
                filepath = Path("data/cache/voice") / filename
                
                await FileUtils.ensure_directory(filepath.parent)
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(audio_buffer.read())
                    
                return filepath
                
        except Exception as e:
            print(f"Error creating voice message: {e}")
            
        return None