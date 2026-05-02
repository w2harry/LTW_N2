"""
Service layer for business logic
"""

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import requests
import json
from ..models import UserProfile, Post, Comment, Category, Notification
from ..utils import ValidationUtils, OTPManager


class AuthenticationService:
    """Handles authentication logic"""
    
    @staticmethod
    def register_user(username, email, password, first_name='', last_name=''):
        """
        Register new user
        Returns: (success, message, user_object)
        """
        try:
            # Check if user exists
            if User.objects.filter(username=username).exists():
                return False, "Tên đăng nhập đã tồn tại", None
            
            if User.objects.filter(email=email).exists():
                return False, "Email đã được đăng ký", None
            
            # Validate inputs
            try:
                ValidationUtils.validate_username(username)
                ValidationUtils.validate_email(email)
                ValidationUtils.validate_password_strength(password)
            except Exception as e:
                return False, str(e), None
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile
            UserProfile.objects.create(user=user)
            
            return True, "Đăng ký thành công", user
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate user
        Returns: authenticated user or None
        """
        user = authenticate(username=username, password=password)
        return user
    
    @staticmethod
    def reset_password(user, new_password):
        """
        Reset user password
        Returns: (success, message)
        """
        try:
            ValidationUtils.validate_password_strength(new_password)
            user.set_password(new_password)
            user.save()
            return True, "Đổi mật khẩu thành công"
        except Exception as e:
            return False, str(e)


class PostService:
    """Handles post-related business logic"""
    
    @staticmethod
    def create_post(user, category, title, content, image=None, privacy='public'):
        """
        Create new post
        Returns: (success, message, post_object)
        """
        try:
            post = Post.objects.create(
                author=user,
                category=category,
                title=title,
                content=content,
                image=image,
                privacy=privacy
            )
            return True, "Bài viết đã được tạo", post
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    @staticmethod
    def get_posts_by_category(category_id, page=1, per_page=10):
        """Get posts filtered by category with pagination"""
        posts = Post.objects.filter(
            category_id=category_id,
            is_hidden=False
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-created_at')
        
        return posts
    
    @staticmethod
    def get_trending_posts(limit=5):
        """Get trending posts based on comments and likes"""
        posts = Post.objects.filter(
            is_hidden=False
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count', '-created_at')[:limit]
        
        return posts
    
    @staticmethod
    def search_posts(query):
        """Search posts by title or content"""
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_hidden=False
        ).order_by('-created_at')
        
        return posts


class CommentService:
    """Handles comment-related business logic"""
    
    @staticmethod
    def create_comment(user, post, content):
        """
        Create new comment
        Returns: (success, message, comment_object)
        """
        try:
            comment = Comment.objects.create(
                author=user,
                post=post,
                content=content
            )
            return True, "Bình luận đã được tạo", comment
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    @staticmethod
    def get_post_comments(post_id, page=1, per_page=10):
        """Get comments for a post with pagination"""
        comments = Comment.objects.filter(
            post_id=post_id,
            is_hidden=False
        ).order_by('created_at')
        
        return comments


class NotificationService:
    """Handles notification logic"""
    
    @staticmethod
    def create_notification(recipient, notification_type, title, message, post=None, comment=None):
        """
        Create notification for user
        Returns: notification object
        """
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            post=post,
            comment=comment
        )
        return notification
    
    @staticmethod
    def get_user_notifications(user_id):
        """Get unread notifications for user"""
        notifications = Notification.objects.filter(
            recipient_id=user_id,
            is_read=False
        ).order_by('-created_at')
        
        return notifications
    
    @staticmethod
    def update_notification(notification_id, user_id, **kwargs):
        """
        Update notification fields
        Returns: (success, message, notification_object)
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient_id=user_id)
            
            # Only allow editing title and message
            allowed_fields = ['title', 'message']
            for field in allowed_fields:
                if field in kwargs:
                    setattr(notification, field, kwargs[field])
            
            notification.save()
            return True, "Cập nhật thông báo thành công", notification
        except Notification.DoesNotExist:
            return False, "Thông báo không tồn tại", None
        except Exception as e:
            return False, f"Lỗi: {str(e)}", None
    
    @staticmethod
    def delete_notification(notification_id, user_id):
        """
        Delete notification for user
        Returns: (success, message)
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient_id=user_id)
            notification.delete()
            return True, "Xóa thông báo thành công"
        except Notification.DoesNotExist:
            return False, "Thông báo không tồn tại"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    @staticmethod
    def delete_multiple_notifications(notification_ids, user_id):
        """
        Delete multiple notifications for user
        Returns: (success, message, deleted_count)
        """
        try:
            deleted_count, _ = Notification.objects.filter(
                id__in=notification_ids,
                recipient_id=user_id
            ).delete()
            return True, "Xóa thông báo thành công", deleted_count
        except Exception as e:
            return False, f"Lỗi: {str(e)}", 0
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a single notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, recipient_id=user_id)
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
            return True, "Cập nhật thành công"
        except Notification.DoesNotExist:
            return False, "Thông báo không tồn tại"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"


class EmailService:
    """Handles email sending via EmailJS"""
    
    @staticmethod
    def send_otp_email(email, otp_code):
        """Send OTP via EmailJS email"""
        try:
            # EmailJS API endpoint
            emailjs_api_url = 'https://api.emailjs.com/api/v1.0/email/send'
            
            # Prepare EmailJS request
            data = {
                'service_id': settings.EMAILJS_SERVICE_ID,
                'template_id': settings.EMAILJS_TEMPLATE_ID,
                'user_id': settings.EMAILJS_USER_ID,
                'accessToken': settings.EMAILJS_PRIVATE_KEY,
                'template_params': {
                    'email': email,
                    'OTP': otp_code
                }
            }
            
            # Send request to EmailJS
            response = requests.post(
                emailjs_api_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✓ OTP email sent successfully to {email}")
                return True
            else:
                print(f"✗ EmailJS error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending OTP email: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        try:
            emailjs_api_url = 'https://api.emailjs.com/api/v1.0/email/send'
            
            data = {
                'service_id': settings.EMAILJS_SERVICE_ID,
                'template_id': settings.EMAILJS_TEMPLATE_ID,
                'user_id': settings.EMAILJS_USER_ID,
                'accessToken': settings.EMAILJS_PRIVATE_KEY,
                'template_params': {
                    'email': user.email,
                    'OTP': f'Welcome {user.first_name or user.username}!'
                }
            }
            
            response = requests.post(
                emailjs_api_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")
            return False
