from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Category, Post, PostImage, Comment, UserProfile, OTPToken, Report, Notification, PostVerification
)

CATEGORY_COLOR_MAP = {
    'pink': '#c9507f',
    'blue': '#3b82f6',
    'teal': '#14b8a6',
    'orange': '#f97316',
    'purple': '#a855f7',
    'green': '#10b981',
}

REPORT_TYPE_COLOR_MAP = {
    'false': '#ef4444',
    'sexual': '#db2777',
    'forbidden': '#b91c1c',
    'offensive': '#f97316',
    'fake_news': '#eab308',
    'spam': '#94a3b8',
    'violence': '#dc2626',
    'other': '#6b7280',
}

REPORT_TYPE_LABEL_MAP = {
    'false': 'Sai sự thật hoặc lừa gạt',
    'sexual': 'Khiêu dâm',
    'forbidden': 'Nội dung bị cấm',
    'offensive': 'Phản cảm',
    'fake_news': 'Tin tức bị sai lệch',
    'spam': 'Tin rác',
    'violence': 'Bạo lực',
    'other': 'Khác',
}


class ProcessedStatusFilter(admin.SimpleListFilter):
    title = 'Trạng thái xử lý'
    parameter_name = 'processed_status'

    def lookups(self, request, model_admin):
        return (
            ('processed', 'Đã xử lý'),
            ('unprocessed', 'Chưa xử lý'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'processed':
            return queryset.filter(is_processed=True)
        if value == 'unprocessed':
            return queryset.filter(is_processed=False)
        return queryset

# Tùy chỉnh trang admin
admin.site.site_header = "MomCare Forum - Quản trị hệ thống"
admin.site.site_title = "MomCare Admin"
admin.site.index_title = ""

_original_each_context = admin.site.each_context


def _momcare_each_context(request):
    context = _original_each_context(request)
    context.update({
        'mc_total_users': User.objects.count(),
        'mc_total_categories': Category.objects.count(),
        'mc_total_reports': Report.objects.count(),
    })
    return context


admin.site.each_context = _momcare_each_context

# Inline cho Comments
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'content', 'verified_by_expert', 'is_hidden', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ('image', 'alt_text', 'order', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('order', 'created_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('colored_name', 'post_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('color_dot', 'created_at')
    search_fields = ('name', 'slug')
    ordering = ('-created_at',)
    actions = ['delete_selected_categories']
    
    def colored_name(self, obj):
        color = CATEGORY_COLOR_MAP.get(obj.color_dot, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.name
        )
    colored_name.short_description = 'Tên danh mục'
    
    def post_count(self, obj):
        count = obj.posts.count()
        return format_html(
            '<span style="background: #e0f2fe; padding: 3px 8px; border-radius: 12px;">{} bài</span>',
            count
        )
    post_count.short_description = 'Số bài viết'

    def delete_model(self, request, obj):
        if obj.posts.exists():
            self.message_user(
                request,
                f'Không thể xóa danh mục "{obj.name}" vì danh mục đang có bài viết.',
                level=messages.ERROR,
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        blocked_names = []
        deletable_ids = []
        for category in queryset:
            if category.posts.exists():
                blocked_names.append(category.name)
            else:
                deletable_ids.append(category.id)

        if blocked_names:
            self.message_user(
                request,
                'Không thể xóa các danh mục đang có bài viết: ' + ', '.join(blocked_names),
                level=messages.ERROR,
            )

        if deletable_ids:
            super().delete_queryset(request, queryset.filter(id__in=deletable_ids))

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Disable Django's default delete_selected action to avoid protected-object permission screen.
        actions.pop('delete_selected', None)
        return actions

    def delete_selected_categories(self, request, queryset):
        blocked_names = []
        deletable = []

        for category in queryset:
            if category.posts.exists():
                blocked_names.append(category.name)
            else:
                deletable.append(category)

        if blocked_names:
            self.message_user(
                request,
                'Không thể xóa danh mục đang có bài viết: ' + ', '.join(blocked_names),
                level=messages.ERROR,
            )

        deleted_count = 0
        for category in deletable:
            category.delete()
            deleted_count += 1

        if deleted_count:
            self.message_user(
                request,
                f'Đã xóa {deleted_count} danh mục không chứa bài viết.',
                level=messages.SUCCESS,
            )

    delete_selected_categories.short_description = 'Xóa danh mục đã chọn (bỏ qua danh mục đang có bài viết)'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title_display', 'author_display', 'category_display', 'privacy_display', 'status_display', 'report_count', 'created_at_display')
    list_filter = ('category', 'verified_by_expert', 'privacy', 'is_hidden', 'created_at')
    search_fields = ('title', 'content', 'author__username', 'author__email')
    list_select_related = ('author', 'category', 'verified_by')
    readonly_fields = ('created_at', 'updated_at', 'verified_at', 'like_count_display', 'comment_count_display')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [PostImageInline]
    
    fieldsets = (
        ('Nội dung bài viết', {
            'fields': ('title', 'content', 'category', 'author', 'image')
        }),
        ('Chế độ và ẩn', {
            'fields': ('privacy', 'is_hidden')
        }),
        ('Kiểm duyệt', {
            'fields': ('verified_by_expert', 'verification_reason', 'verified_by', 'verified_at'),
            'description': 'Chỉ các bác sĩ có thể kiểm duyệt bài viết'
        }),
        ('Thống kê', {
            'fields': ('like_count_display', 'comment_count_display', 'report_count'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_posts', 'unverify_posts', 'hide_posts', 'unhide_posts']
    
    def title_display(self, obj):
        return format_html(
            '<strong>{}</strong>',
            obj.title[:50] + ('...' if len(obj.title) > 50 else '')
        )
    title_display.short_description = 'Tiêu đề'
    
    def author_display(self, obj):
        user_change_url = reverse('admin:auth_user_change', args=[obj.author.id])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            user_change_url, obj.author.username
        )
    author_display.short_description = 'Tác giả'
    
    def category_display(self, obj):
        color = CATEGORY_COLOR_MAP.get(obj.category.color_dot, '#000000')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 12px;">{}</span>',
            color, obj.category.name
        )
    category_display.short_description = 'Danh mục'
    
    def privacy_display(self, obj):
        if obj.privacy == 'public':
            tag = '<span style="background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 8px;">Công khai</span>'
        else:
            tag = '<span style="background: #f3e8ff; color: #6b21a8; padding: 4px 8px; border-radius: 8px;">Ẩn danh</span>'
        return format_html(tag)
    privacy_display.short_description = 'Chế độ'
    
    def status_display(self, obj):
        if obj.is_hidden:
            return format_html('<span style="color: red; font-weight: bold;">Bị ẩn</span>')
        elif obj.verified_by_expert:
            return format_html('<span style="color: green; font-weight: bold;">Đã kiểm duyệt</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">Chờ duyệt</span>')
    status_display.short_description = 'Trạng thái'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y H:i')
    created_at_display.short_description = 'Ngày tạo'
    
    def like_count_display(self, obj):
        return format_html('{} lượt thích', obj.likes.count())
    like_count_display.short_description = 'Lượt thích'
    
    def comment_count_display(self, obj):
        return format_html('{} bình luận', obj.comments.count())
    comment_count_display.short_description = 'Bình luận'
    
    def verify_posts(self, request, queryset):
        updated = 0
        for post in queryset:
            PostVerification.objects.update_or_create(
                post=post,
                doctor=request.user,
                defaults={
                    'verification_reasons': post.verification_reasons or post.verification_reason or 'expert',
                    'verification_note': post.verification_note or 'Kiểm duyệt từ Django Admin.',
                }
            )
            post.refresh_verification_status(save=True)
            updated += 1
        self.message_user(request, f'{updated} bài viết đã được kiểm duyệt')
    verify_posts.short_description = 'Kiểm duyệt bài viết chọn'
    
    def unverify_posts(self, request, queryset):
        updated = 0
        for post in queryset:
            deleted, _ = PostVerification.objects.filter(post=post).delete()
            if deleted:
                updated += 1
            post.refresh_verification_status(save=True)
        self.message_user(request, f'{updated} bài viết đã gỡ kiểm duyệt')
    unverify_posts.short_description = 'Gỡ kiểm duyệt'
    
    def hide_posts(self, request, queryset):
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f'{updated} bài viết đã được ẩn')
    hide_posts.short_description = 'Ẩn bài viết'
    
    def unhide_posts(self, request, queryset):
        updated = queryset.update(is_hidden=False)
        self.message_user(request, f'{updated} bài viết đã hiển thị')
    unhide_posts.short_description = 'Hiển thị bài viết'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_display', 'post_display', 'content_preview', 'verified_display', 'is_hidden', 'created_at_display')
    list_filter = ('verified_by_expert', 'is_hidden', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    list_select_related = ('author', 'post', 'verified_by')
    readonly_fields = ('created_at', 'updated_at', 'verified_at', 'like_count_display')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Bình luận', {
            'fields': ('author', 'post', 'content')
        }),
        ('Kiểm duyệt', {
            'fields': ('verified_by_expert', 'verification_reason', 'verified_by', 'verified_at')
        }),
        ('Thống kê', {
            'fields': ('like_count_display', 'report_count', 'is_hidden'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_comments', 'hide_comments']
    
    def author_display(self, obj):
        return format_html('<strong>{}</strong>', obj.author.username)
    author_display.short_description = 'Tác giả'
    
    def post_display(self, obj):
        post_change_url = reverse('admin:forum_post_change', args=[obj.post.id])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            post_change_url, obj.post.title[:40] + ('...' if len(obj.post.title) > 40 else '')
        )
    post_display.short_description = 'Bài viết'
    
    def content_preview(self, obj):
        return obj.content[:60] + ('...' if len(obj.content) > 60 else '')
    content_preview.short_description = 'Nội dung'
    
    def verified_display(self, obj):
        return format_html('<span style="color: green;">Đã duyệt</span>' if obj.verified_by_expert else '<span style="color: gray;">Chờ</span>')
    verified_display.short_description = 'Kiểm duyệt'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y H:i')
    created_at_display.short_description = 'Ngày tạo'
    
    def like_count_display(self, obj):
        return format_html('{} lượt thích', obj.likes.count())
    like_count_display.short_description = 'Lượt thích'
    
    def verify_comments(self, request, queryset):
        updated = queryset.update(verified_by_expert=True, verified_by=request.user)
        self.message_user(request, f'{updated} bình luận đã được kiểm duyệt')
    verify_comments.short_description = 'Kiểm duyệt bình luận'
    
    def hide_comments(self, request, queryset):
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f'{updated} bình luận đã được ẩn')
    hide_comments.short_description = 'Ẩn bình luận'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'user_type_display', 'post_count', 'created_at_display')
    list_filter = ('user_type', 'is_verified_doctor', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'post_count_display', 'comment_count_display', 'user_email_display')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Thông tin người dùng', {
            'fields': ('user', 'user_email_display', 'user_type')
        }),
        ('Bác sĩ', {
            'fields': ('is_verified_doctor', 'bio'),
            'description': 'Xác minh bác sĩ qua địa chỉ email hoặc tài liệu'
        }),
        ('Thống kê', {
            'fields': ('post_count_display', 'comment_count_display'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_doctors', 'unverify_doctors']
    
    def user_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: gray;">{}</small>',
            obj.user.username, obj.user.email
        )
    user_display.short_description = 'Người dùng'

    def user_email_display(self, obj):
        return obj.user.email or '—'
    user_email_display.short_description = 'Email'
    
    def user_type_display(self, obj):
        types = {
            'user': ('<span style="background: #e0f2fe; color: #0c4a6e; padding: 4px 8px; border-radius: 8px;">Người dùng</span>', 'user'),
            'doctor': ('<span style="background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 8px;">Bác sĩ</span>', 'doctor'),
            'admin': ('<span style="background: #ffe4e6; color: #9f1239; padding: 4px 8px; border-radius: 8px;">Admin</span>', 'admin'),
        }
        tag, _ = types.get(obj.user_type, (obj.user_type, None))
        return format_html(tag)
    user_type_display.short_description = 'Loại'
    
    def post_count(self, obj):
        count = obj.user.posts.count()
        return format_html('{}', count)
    post_count.short_description = 'Bài viết'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y')
    created_at_display.short_description = 'Ngày tạo'
    
    def post_count_display(self, obj):
        return obj.user.posts.count()
    post_count_display.short_description = 'Tổng bài viết'
    
    def comment_count_display(self, obj):
        return obj.user.comments.count()
    comment_count_display.short_description = 'Tổng bình luận'
    
    def verify_doctors(self, request, queryset):
        updated = queryset.filter(user_type='doctor').update(is_verified_doctor=True)
        self.message_user(request, f'{updated} bác sĩ đã được xác minh')
    verify_doctors.short_description = 'Xác minh bác sĩ'
    
    def unverify_doctors(self, request, queryset):
        updated = queryset.filter(user_type='doctor').update(is_verified_doctor=False)
        self.message_user(request, f'{updated} bác sĩ đã gỡ xác minh')
    unverify_doctors.short_description = 'Gỡ xác minh bác sĩ'

@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_display = ('email_display', 'otp_type_display', 'status_display', 'created_at_display', 'expires_at_display')
    list_filter = ('otp_type', 'is_used', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('otp_code', 'created_at', 'expires_at', 'age_display')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('OTP', {
            'fields': ('email', 'otp_code', 'otp_type')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'expires_at', 'age_display')
        }),
        ('Sử dụng', {
            'fields': ('is_used',)
        }),
    )
    
    def email_display(self, obj):
        return format_html('<strong>{}</strong>', obj.email)
    email_display.short_description = 'Email'
    
    def otp_type_display(self, obj):
        types = {
            'register': '<span style="background: #3b82f6; color: white; padding: 4px 8px; border-radius: 8px;">Đăng ký</span>',
            'forgot_password': '<span style="background: #f97316; color: white; padding: 4px 8px; border-radius: 8px;">Quên mật khẩu</span>',
        }
        return format_html(types.get(obj.otp_type, obj.otp_type))
    otp_type_display.short_description = 'Loại'
    
    def status_display(self, obj):
        from datetime import datetime, timezone
        is_expired = obj.expires_at < datetime.now(timezone.utc)
        if obj.is_used:
            return format_html('<span style="color: green;">Đã sử dụng</span>')
        elif is_expired:
            return format_html('<span style="color: red;">Hết hạn</span>')
        else:
            return format_html('<span style="color: orange;">Chờ (hợp lệ)</span>')
    status_display.short_description = 'Trạng thái'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y H:i:s')
    created_at_display.short_description = 'Tạo lúc'
    
    def expires_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.expires_at, 'd/m/Y H:i:s')
    expires_at_display.short_description = 'Hết hạn lúc'
    
    def age_display(self, obj):
        from datetime import datetime, timezone
        age = datetime.now(timezone.utc) - obj.created_at
        minutes = int(age.total_seconds() / 60)
        seconds = int(age.total_seconds() % 60)
        return f'{minutes}m {seconds}s'
    age_display.short_description = 'Tuổi'

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'post_title_link',
        'post_author_display',
        'post_privacy_display',
        'post_report_count_display',
        'reporter_display',
        'reason_display',
    )
    list_filter = ('report_type', ProcessedStatusFilter, 'created_at')
    search_fields = ('reporter__username', 'reason', 'post__title', 'comment__content')
    list_select_related = ('reporter', 'post', 'comment', 'processed_by')
    readonly_fields = ('created_at', 'updated_at', 'processed_at', 'reason_display')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Báo cáo', {
            'fields': ('reporter', 'report_type', 'reason_display')
        }),
        ('Đối tượng báo cáo', {
            'fields': ('post', 'comment'),
            'description': 'Báo cáo cho bài viết hoặc bình luận'
        }),
        ('Xử lý', {
            'fields': ('is_processed',),
            'classes': ('wide',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_processed', 'mark_not_processed']
    
    def post_title_link(self, obj):
        if not obj.post_id:
            return '(Bài viết đã bị xóa)'
        post_url = reverse('post_detail', args=[obj.post_id])
        return format_html('<a href="{}" target="_blank" rel="noopener"><strong>{}</strong></a>', post_url, obj.post.title)
    post_title_link.short_description = 'Tiêu đề'

    def post_author_display(self, obj):
        if not obj.post_id:
            return '—'
        return format_html('@{}', obj.post.author.username)
    post_author_display.short_description = 'Tác giả'

    def post_privacy_display(self, obj):
        if not obj.post_id:
            return '—'
        return 'Ẩn danh' if obj.post.privacy == 'anonymous' else 'Công khai'
    post_privacy_display.short_description = 'Chế độ hiển thị'

    def post_report_count_display(self, obj):
        if not obj.post_id:
            return 0
        return obj.post.report_count
    post_report_count_display.short_description = 'Số lần báo cáo'

    def reporter_display(self, obj):
        return format_html('<strong>{}</strong>', obj.reporter.get_full_name() or obj.reporter.username)
    reporter_display.short_description = 'Người báo cáo'
    
    def report_type_display(self, obj):
        color = REPORT_TYPE_COLOR_MAP.get(obj.report_type, '#000000')
        label = REPORT_TYPE_LABEL_MAP.get(obj.report_type, obj.get_report_type_display())
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 8px;">{}</span>',
            color, label
        )
    report_type_display.short_description = 'Loại báo cáo'
    
    def status_display(self, obj):
        return format_html('<span style="color: green;">Đã xử lý</span>' if obj.is_processed else '<span style="color: orange;">Chờ</span>')
    status_display.short_description = 'Trạng thái'
    
    def on_item_display(self, obj):
        if obj.post:
            post_change_url = reverse('admin:forum_post_change', args=[obj.post.id])
            return format_html('<a href="{}"><strong>Bài viết</strong></a>', post_change_url)
        elif obj.comment:
            comment_change_url = reverse('admin:forum_comment_change', args=[obj.comment.id])
            return format_html('<a href="{}"><strong>Bình luận</strong></a>', comment_change_url)
        return '—'
    on_item_display.short_description = 'Mục tiêu'
    
    def processed_by_display(self, obj):
        if obj.processed_by:
            return format_html('<strong>{}</strong>', obj.processed_by.username)
        return '—'
    processed_by_display.short_description = 'Xử lý bởi'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y H:i')
    created_at_display.short_description = 'Ngày báo cáo'
    
    def reason_display(self, obj):
        if obj.reason:
            return f'{obj.get_report_type_display()}: {obj.reason}'
        return obj.get_report_type_display()
    reason_display.short_description = 'Lý do'
    
    def mark_processed(self, request, queryset):
        updated = queryset.update(is_processed=True, processed_by=request.user)
        self.message_user(request, f'{updated} báo cáo đã được đánh dấu là đã xử lý')
    mark_processed.short_description = 'Đánh dấu là đã xử lý'
    
    def mark_not_processed(self, request, queryset):
        updated = queryset.update(is_processed=False, processed_by=None)
        self.message_user(request, f'{updated} báo cáo chưa xử lý')
    mark_not_processed.short_description = 'Đánh dấu là chưa xử lý'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient_display', 'type_display', 'title_display', 'read_status', 'created_at_display')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    list_select_related = ('recipient', 'post', 'comment')
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Thông báo', {
            'fields': ('recipient', 'title', 'message', 'notification_type')
        }),
        ('Liên quan', {
            'fields': ('post', 'comment'),
            'classes': ('collapse',)
        }),
        ('Đọc', {
            'fields': ('is_read', 'read_at'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def recipient_display(self, obj):
        return format_html('<strong>{}</strong>', obj.recipient.username)
    recipient_display.short_description = 'Người nhận'
    
    def type_display(self, obj):
        types = {
            'comment': '<span style="background: #3b82f6; color: white; padding: 4px 8px; border-radius: 8px;">Bình luận mới</span>',
            'verified': '<span style="background: #10b981; color: white; padding: 4px 8px; border-radius: 8px;">Kiểm duyệt</span>',
            'report_processed': '<span style="background: #f97316; color: white; padding: 4px 8px; border-radius: 8px;">Báo cáo xử lý</span>',
            'system': '<span style="background: #8b5cf6; color: white; padding: 4px 8px; border-radius: 8px;">Hệ thống</span>',
        }
        return format_html(types.get(obj.notification_type, obj.notification_type))
    type_display.short_description = 'Loại'
    
    def title_display(self, obj):
        return format_html('<strong>{}</strong>', obj.title[:50] + ('...' if len(obj.title) > 50 else ''))
    title_display.short_description = 'Tiêu đề'
    
    def read_status(self, obj):
        return format_html('<span style="color: green;">Đã đọc</span>' if obj.is_read else '<span style="color: orange;">Chưa đọc</span>')
    read_status.short_description = 'Trạng thái'
    
    def created_at_display(self, obj):
        from django.utils.dateformat import format as format_date
        return format_date(obj.created_at, 'd/m/Y H:i')
    created_at_display.short_description = 'Ngày gửi'
    
    def mark_as_read(self, request, queryset):
        from datetime import datetime, timezone
        updated = queryset.update(is_read=True, read_at=datetime.now(timezone.utc))
        self.message_user(request, f'{updated} thông báo đã được đánh dấu là đã đọc')
    mark_as_read.short_description = 'Đánh dấu là đã đọc'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} thông báo đã đánh dấu là chưa đọc')
    mark_as_unread.short_description = 'Đánh dấu là chưa đọc'


# Remove comment and notification management from admin menu per product requirements.
try:
    admin.site.unregister(Comment)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Notification)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(OTPToken)
except admin.sites.NotRegistered:
    pass
