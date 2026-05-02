from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class Category(models.Model):
    COLOR_CHOICES = [
        ('pink', 'Hồng'),
        ('blue', 'Xanh lam'),
        ('green', 'Xanh lá'),
        ('orange', 'Cam'),
        ('purple', 'Tím'),
        ('teal', 'Xanh mòng két'),
    ]

    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    color_dot = models.CharField(max_length=20, choices=COLOR_CHOICES, default='pink', verbose_name="Màu chấm")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"


class UserProfile(models.Model):
    USER_TYPES = [
        ('user', 'Người dùng'),
        ('doctor', 'Bác sĩ/Chuyên gia'),
        ('admin', 'Quản trị viên'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='user', verbose_name="Loại tài khoản")
    is_verified_doctor = models.BooleanField(default=False, verbose_name="Bác sĩ đã xác minh")
    doctor_title = models.CharField(max_length=120, blank=True, verbose_name="Chức danh chuyên môn")
    bio = models.TextField(blank=True, max_length=500, verbose_name="Tiểu sử")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Ảnh đại diện")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    class Meta:
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Hồ sơ người dùng"


class Post(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Công khai'),
        ('anonymous', 'Ẩn danh'),
    ]
    
    VERIFICATION_REASONS = [
        ('accurate', 'Bài viết chứa nội dung phù hợp với kiến thức y khoa hiện hành'),
        ('safe', 'Thông tin trong bài viết an toàn cho mẹ và bé'),
        ('useful', 'Bài viết cung cấp kiến thức chăm sóc sức khỏe hữu ích'),
        ('nutrition', 'Thông tin dinh dưỡng đã được kiểm chứng'),
        ('confirmed', 'Thông tin trong bài viết đã được bác sĩ xác nhận'),
        ('reference', 'Bài viết có giá trị tham khảo'),
        ('expert', 'Nội dung phù hợp với khuyến nghị của chuyên gia'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="posts", verbose_name="Danh mục")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", verbose_name="Người đăng")
    
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public', verbose_name="Chế độ hiển thị")
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name="Hình ảnh mô tả")
    
    verified_by_expert = models.BooleanField(default=False, verbose_name="Được chuyên gia kiểm duyệt")
    verification_reason = models.CharField(max_length=20, choices=VERIFICATION_REASONS, blank=True, verbose_name="Lý do kiểm duyệt")
    verification_reasons = models.TextField(blank=True, verbose_name="Danh sách lý do kiểm duyệt")
    verification_note = models.TextField(blank=True, verbose_name="Ghi chú kiểm duyệt")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_posts', verbose_name="Người kiểm duyệt")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian kiểm duyệt")
    
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    report_count = models.IntegerField(default=0, verbose_name="Số lần báo cáo")
    is_hidden = models.BooleanField(default=False, verbose_name="Ẩn bài viết")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_likes(self):
        return self.likes.count()

    @property
    def display_image_url(self):
        """Return direct URL for both local files and absolute Cloudinary URLs."""
        if not self.image:
            return ''
        image_name = getattr(self.image, 'name', '')
        if isinstance(image_name, str) and image_name.startswith(('http://', 'https://')):
            return image_name
        try:
            return self.image.url
        except Exception:
            return image_name or ''

    def __str__(self):
        return self.title

    @property
    def verification_reason_labels(self):
        reason_map = dict(self.VERIFICATION_REASONS)
        raw = (self.verification_reasons or '').strip()
        if raw:
            codes = [code.strip() for code in raw.split(',') if code.strip()]
        elif self.verification_reason:
            codes = [self.verification_reason]
        else:
            codes = []
        return [reason_map.get(code, code) for code in codes]

    def refresh_verification_status(self, save=True):
        """Sync legacy verification fields from latest verification record."""
        latest = self.verifications.select_related('doctor').order_by('-verified_at').first()
        if latest:
            self.verified_by_expert = True
            self.verified_by = latest.doctor
            self.verified_at = latest.verified_at
            self.verification_reasons = latest.verification_reasons
            self.verification_reason = latest.primary_reason
            self.verification_note = latest.verification_note
        else:
            self.verified_by_expert = False
            self.verified_by = None
            self.verified_at = None
            self.verification_reasons = ''
            self.verification_reason = ''
            self.verification_note = ''

        if save:
            self.save(update_fields=[
                'verified_by_expert',
                'verified_by',
                'verified_at',
                'verification_reasons',
                'verification_reason',
                'verification_note',
            ])

    class Meta:
        ordering = ['-created_at']


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images', verbose_name='Bài viết')
    image = models.ImageField(upload_to='posts/', verbose_name='Hình ảnh')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Mô tả ảnh')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} of post {self.post_id}"

    @property
    def display_image_url(self):
        """Return direct URL for both local files and absolute Cloudinary URLs."""
        if not self.image:
            return ''
        image_name = getattr(self.image, 'name', '')
        if isinstance(image_name, str) and image_name.startswith(('http://', 'https://')):
            return image_name
        try:
            return self.image.url
        except Exception:
            return image_name or ''

    class Meta:
        verbose_name = 'Hình ảnh bài viết'
        verbose_name_plural = 'Hình ảnh bài viết'
        ordering = ['order', 'created_at']


class PostVerification(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='verifications', verbose_name='Bài viết')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_verifications', verbose_name='Bác sĩ kiểm duyệt')
    verification_reasons = models.TextField(blank=True, verbose_name='Danh sách lý do kiểm duyệt')
    custom_reasons = models.TextField(blank=True, verbose_name='Lý do bổ sung')
    verification_note = models.TextField(blank=True, verbose_name='Ghi chú kiểm duyệt')
    verified_at = models.DateTimeField(default=timezone.now, verbose_name='Thời gian kiểm duyệt')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lịch sử kiểm duyệt bài viết'
        verbose_name_plural = 'Lịch sử kiểm duyệt bài viết'
        ordering = ['-verified_at']
        constraints = [
            models.UniqueConstraint(fields=['post', 'doctor'], name='uniq_post_doctor_verification')
        ]

    @property
    def reason_codes(self):
        raw = (self.verification_reasons or '').strip()
        if not raw:
            return []
        return [code.strip() for code in raw.split(',') if code.strip()]

    @property
    def primary_reason(self):
        codes = self.reason_codes
        return codes[0] if codes else ''

    @property
    def reason_labels(self):
        reason_map = dict(Post.VERIFICATION_REASONS)
        return [reason_map.get(code, code) for code in self.reason_codes]

    @property
    def custom_reason_items(self):
        raw = (self.custom_reasons or '').strip()
        if not raw:
            return []

        # Each line is treated as one custom reason. Commas are also supported for convenience.
        items = []
        for line in raw.splitlines():
            chunks = [part.strip() for part in line.split(',') if part.strip()]
            for chunk in chunks:
                if chunk not in items:
                    items.append(chunk)
        return items

    @property
    def all_reason_labels(self):
        labels = []
        for item in self.reason_labels + self.custom_reason_items:
            if item not in labels:
                labels.append(item)
        return labels

    def __str__(self):
        return f"{self.post_id} - {self.doctor.username}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Bài viết")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", verbose_name="Người bình luận")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Bình luận cha'
    )
    content = models.TextField(verbose_name="Nội dung")
    is_anonymous = models.BooleanField(default=False, verbose_name="Bình luận ẩn danh")
    
    verified_by_expert = models.BooleanField(default=False, verbose_name="Được chuyên gia kiểm duyệt")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_comments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)
    report_count = models.IntegerField(default=0, verbose_name="Số lần báo cáo")
    is_hidden = models.BooleanField(default=False, verbose_name="Ẩn bình luận")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    class Meta:
        ordering = ['created_at']

    def display_author_name(self, can_view_identity=False):
        if self.is_anonymous and not can_view_identity:
            return 'Người dùng ẩn danh'
        return self.author.get_full_name() or self.author.username


class OTPToken(models.Model):
    OTP_TYPE_CHOICES = [
        ('register', 'Đăng ký'),
        ('forgot_password', 'Quên mật khẩu'),
    ]
    
    email = models.EmailField(verbose_name="Email")
    otp_code = models.CharField(max_length=6, verbose_name="Mã OTP")
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, verbose_name="Loại OTP")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name="Hết hạn")
    is_used = models.BooleanField(default=False, verbose_name="Đã sử dụng")
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.email} ({self.otp_type})"

    class Meta:
        verbose_name = "Mã OTP"
        verbose_name_plural = "Mã OTP"


class Report(models.Model):
    REPORT_TYPES = [
        ('false', 'Sai sự thật hoặc lừa gạt'),
        ('sexual', 'Khiêu dâm'),
        ('forbidden', 'Nội dung bị cấm'),
        ('offensive', 'Phản cảm'),
        ('violence', 'Bạo lực'),
        ('fake_news', 'Tin tức bị sai lệch'),
        ('spam', 'Spam'),
        ('other', 'Khác'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', verbose_name="Người báo cáo")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reports', verbose_name="Bài viết")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports', verbose_name="Bình luận")
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Loại vi phạm")
    reason = models.TextField(blank=True, verbose_name="Lý do chi tiết")
    
    is_processed = models.BooleanField(default=False, verbose_name="Đã xử lý")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_reports')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        target = self.post or self.comment
        return f"Report {self.get_report_type_display()} - {target}"

    class Meta:
        verbose_name = "Báo cáo vi phạm"
        verbose_name_plural = "Báo cáo vi phạm"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'Bình luận mới'),
        ('verified', 'Bài viết được kiểm duyệt'),
        ('report_processed', 'Báo cáo được xử lý'),
        ('system', 'Thông báo hệ thống'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Người nhận")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Loại thông báo")
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    message = models.TextField(verbose_name="Nội dung")
    
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    is_read = models.BooleanField(default=False, verbose_name="Đã đọc")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đọc")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"


class AdminActivityLog(models.Model):
    ACTION_TYPES = [
        ('user_delete', 'Xóa người dùng'),
        ('user_role_change', 'Thay đổi vai trò'),
        ('post_delete', 'Xóa bài viết'),
        ('post_hide', 'Ẩn bài viết'),
        ('post_verify', 'Verify bài viết'),
        ('comment_delete', 'Xóa bình luận'),
        ('comment_hide', 'Ẩn bình luận'),
        ('report_process', 'Xử lý báo cáo'),
        ('notification_create', 'Tạo thông báo hệ thống'),
        ('settings_change', 'Thay đổi cài đặt'),
        ('category_manage', 'Quản lý danh mục'),
        ('other', 'Khác'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions', verbose_name="Quản trị viên")
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES, verbose_name="Loại hành động")
    action_description = models.TextField(verbose_name="Mô tả hành động")
    
    # Related objects
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_target_actions', verbose_name="Người dùng liên quan")
    target_post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions', verbose_name="Bài viết liên quan")
    target_comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions', verbose_name="Bình luận liên quan")
    
    # Status
    status = models.CharField(max_length=20, choices=[('success', 'Thành công'), ('failed', 'Lỗi')], default='success')
    error_message = models.TextField(blank=True, verbose_name="Thông báo lỗi")
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Địa chỉ IP")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_type_display()} by {self.admin.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lịch sử hoạt động admin"
        verbose_name_plural = "Lịch sử hoạt động admin"
        indexes = [
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]


class SystemSettings(models.Model):
    # Singleton pattern - only one record
    SETTING_KEYS = [
        ('max_posts_per_day', 'Tối đa bài viết/ngày'),
        ('max_comments_per_day', 'Tối đa bình luận/ngày'),
        ('report_threshold', 'Ngưỡng báo cáo để ẩn'),
        ('email_notifications', 'Bật thông báo email'),
        ('moderation_required', 'Yêu cầu duyệt bài viết'),
        ('auto_ban_threshold', 'Tự động ban sau X báo cáo'),
        ('maintenance_mode', 'Chế độ bảo trì'),
        ('site_announcement', 'Thông báo website'),
    ]
    
    key = models.CharField(max_length=50, unique=True, choices=SETTING_KEYS, verbose_name="Khóa cài đặt")
    value = models.TextField(verbose_name="Giá trị")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cập nhật bởi")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_key_display()}: {self.value}"

    class Meta:
        verbose_name = "Cài đặt hệ thống"
        verbose_name_plural = "Cài đặt hệ thống"

