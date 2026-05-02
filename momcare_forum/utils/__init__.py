"""
Utility functions for OTP, validation, and common operations
"""

import random
import string
import re
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..models import OTPToken


class OTPManager:
    """Manages OTP generation and validation"""
    
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_otp(email, otp_type, expiry_minutes=1):
        """
        Create OTP token
        Args:
            email: User email
            otp_type: Type of OTP (register, reset_password, etc)
            expiry_minutes: OTP expiry time in minutes
        Returns: OTP code string
        """
        otp_code = OTPManager.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        # Remove existing unused OTP for this email
        OTPToken.objects.filter(
            email=email, 
            otp_type=otp_type, 
            is_used=False
        ).delete()
        
        otp = OTPToken.objects.create(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        
        return otp_code
    
    @staticmethod
    def verify_otp(email, otp_code, otp_type):
        """
        Verify OTP code
        Returns: (is_valid, message)
        """
        try:
            otp = OTPToken.objects.get(
                email=email,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False
            )
            
            if not otp.is_valid():
                return False, "OTP đã hết hạn"
            
            otp.is_used = True
            otp.save()
            return True, "OTP hợp lệ"
            
        except OTPToken.DoesNotExist:
            return False, "OTP không đúng hoặc đã hết hạn"


class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Email không hợp lệ")
        return True
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength. Returns (is_valid, message) tuple"""
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự"
        if not any(char.isupper() for char in password):
            return False, "Mật khẩu phải chứa ít nhất một chữ cái viết hoa"
        if not any(char.isdigit() for char in password):
            return False, "Mật khẩu phải chứa ít nhất một chữ số"
        return True, "Mật khẩu hợp lệ"
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if len(username) < 3:
            raise ValidationError("Tên đăng nhập phải có ít nhất 3 ký tự")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise ValidationError("Tên đăng nhập chỉ được chứa chữ cái, số, dấu chấm, dấu gạch ngang và dấu gạch dưới")
        return True


class StringUtils:
    """String manipulation utilities"""
    
    @staticmethod
    def truncate_text(text, max_length=100, suffix='...'):
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + suffix
    
    @staticmethod
    def sanitize_input(text):
        """Sanitize user input"""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text.strip()
