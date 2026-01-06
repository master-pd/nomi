"""
Security Utilities - Security related functions
"""

import hashlib
import secrets
import string
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64

class SecurityUtils:
    """Security related utilities"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
            
        # Combine password and salt
        salted_password = password + salt
        
        # Create hash
        hash_obj = hashlib.sha256(salted_password.encode())
        password_hash = hash_obj.hexdigest()
        
        return {
            "hash": password_hash,
            "salt": salt
        }
        
    @staticmethod
    def verify_password(password: str, 
                       password_hash: str, 
                       salt: str) -> bool:
        """Verify password against hash"""
        hashed = SecurityUtils.hash_password(password, salt)
        return hashed["hash"] == password_hash
        
    @staticmethod
    def encrypt_data(data: str, key: Optional[str] = None) -> Dict[str, str]:
        """Encrypt data using Fernet"""
        if key is None:
            key = Fernet.generate_key()
        else:
            # Ensure key is proper length
            key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode()).digest()
            )
            
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        
        return {
            "encrypted": encrypted.decode(),
            "key": key.decode()
        }
        
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> Optional[str]:
        """Decrypt data using Fernet"""
        try:
            key_bytes = key.encode()
            fernet = Fernet(key_bytes)
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return None
            
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input"""
        import html
        
        # Escape HTML
        sanitized = html.escape(input_str)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized 
                          if ord(char) >= 32 or char in '\n\r\t')
                          
        return sanitized
        
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
        
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (Bangladeshi format)"""
        import re
        
        patterns = [
            r'^\+8801[3-9]\d{8}$',  # +8801XXXXXXXXX
            r'^01[3-9]\d{8}$',       # 01XXXXXXXXX
            r'^1[3-9]\d{8}$'         # 1XXXXXXXXX
        ]
        
        return any(bool(re.match(pattern, phone)) for pattern in patterns)
        
    @staticmethod
    def generate_api_key() -> str:
        """Generate API key"""
        return secrets.token_urlsafe(32)
        
    @staticmethod
    def mask_sensitive_data(data: str, 
                          visible_chars: int = 4) -> str:
        """Mask sensitive data (like credit cards)"""
        if len(data) <= visible_chars * 2:
            return data
            
        start = data[:visible_chars]
        end = data[-visible_chars:]
        middle = '*' * (len(data) - visible_chars * 2)
        
        return start + middle + end