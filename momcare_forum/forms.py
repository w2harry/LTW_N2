from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, Post, Comment, Report, Notification, SystemSettings, AdminActivityLog


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[validate_password]
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Mật khẩu không khớp.")
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Viết tiểu sử của bạn...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['category', 'title', 'content', 'image', 'privacy']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tiêu đề bài viết'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Nội dung bài viết'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'privacy': forms.Select(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Viết bình luận...'}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'reason']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Mô tả chi tiết lý do báo cáo...'}),
        }


class PasswordResetForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[validate_password]
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Mật khẩu không khớp.")
        
        return cleaned_data


class NotificationForm(forms.ModelForm):
    """Form for creating system notifications (Admin only)"""
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề thông báo'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Nội dung thông báo'
            }),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For system notifications, only allow 'system' type
        self.fields['notification_type'].initial = 'system'


class ChangeUserRoleForm(forms.Form):
    """Form for changing user role"""
    ROLE_CHOICES = [
        ('user', 'Người dùng'),
        ('doctor', 'Bác sĩ/Chuyên gia'),
        ('admin', 'Quản trị viên'),
    ]
    
    user_type = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_verified_doctor = forms.BooleanField(
        required=False,
        label='Xác minh bác sĩ',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class SystemSettingsForm(forms.ModelForm):
    """Form for system settings"""
    class Meta:
        model = SystemSettings
        fields = ['value', 'description']
        widgets = {
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Giá trị cài đặt'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả'
            }),
        }


class BulkPostActionForm(forms.Form):
    """Form for bulk actions on posts"""
    ACTION_CHOICES = [
        ('hide', 'Ẩn bài viết'),
        ('unhide', 'Hiển thị bài viết'),
        ('delete', 'Xóa bài viết'),
        ('verify', 'Verify bài viết'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Lý do (tùy chọn)'
        })
    )


class AdvancedSearchForm(forms.Form):
    """Form for advanced search"""
    SEARCH_TYPE_CHOICES = [
        ('post', 'Bài viết'),
        ('user', 'Người dùng'),
        ('comment', 'Bình luận'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Từ khóa tìm kiếm'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Post.objects.values_list('category', flat=True).distinct(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
