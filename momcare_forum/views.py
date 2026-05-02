from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.db.models.deletion import ProtectedError
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.core.cache import cache
from django.conf import settings
from datetime import datetime
import hashlib
import json
import re
import requests

from .models import (
    Category, Post, PostImage, Comment, UserProfile, OTPToken, 
    Report, Notification, AdminActivityLog, SystemSettings, PostVerification
)
from .forms import (
    UserRegistrationForm, UserProfileForm, PostForm, 
    CommentForm, ReportForm, PasswordResetForm, NotificationForm,
    ChangeUserRoleForm, SystemSettingsForm, BulkPostActionForm,
    AdvancedSearchForm
)
from .utils import OTPManager, ValidationUtils, StringUtils
from .services import (
    AuthenticationService, PostService, CommentService,
    NotificationService, EmailService
)
from .services.cloudinary_service import CloudinaryService

# ========== UTILITY FUNCTIONS (moved to utils.py and services.py) ==========

# For backward compatibility, create aliases to new modules
create_otp = OTPManager.create_otp
verify_otp = OTPManager.verify_otp
validate_email = ValidationUtils.validate_email


def _upload_post_images_to_cloudinary(uploaded_files, user_id):
    """Upload all provided files to Cloudinary and return secure URLs."""
    uploaded_urls = []
    for file_obj in uploaded_files:
        result = CloudinaryService.upload_image(
            file_obj,
            folder=f'momcare/posts/user_{user_id}',
            tags=[f'user_{user_id}', 'post_image'],
        )
        if not result or not result.get('secure_url'):
            raise ValueError('Không thể tải ảnh lên Cloudinary. Vui lòng thử lại.')
        uploaded_urls.append(result['secure_url'])
    return uploaded_urls


# ========== AUTHENTICATION VIEWS ==========
# Note: Login and registration now handled via modal in login_modal.html
# See API endpoints: api_login_validate, api_register_validate

@require_http_methods(['GET', 'POST'])
def user_logout(request):
    """Unified logout handler for web, API, and admin users"""
    logout(request)
    
    # Handle API requests
    is_api = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_api or request.path == '/api/logout/':
        return JsonResponse({'success': True, 'message': 'Đăng xuất thành công!'})
    
    # Handle admin logout
    if request.path == '/admin-logout/':
        response = redirect('admin_login')
        response.delete_cookie('sessionid')
        return response
    
    # Handle regular user logout
    return redirect('forum')

def forgot_password_step1(request):
    """Forgot Password Step 1: Input email"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            context = {'error': 'Vui lòng nhập email'}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_step1.html', context)
        
        if not User.objects.filter(email__iexact=email).exists():
            context = {'error': 'Email không hợp lệ hoặc chưa được đăng ký'}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_step1.html', context)
        
        # Create OTP and send email
        otp_code = create_otp(email, 'forgot_password')
        email_sent = EmailService.send_otp_email(email, otp_code)
        if not email_sent:
            context = {'error': 'Không thể gửi mã OTP lúc này. Vui lòng thử lại sau.'}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_step1.html', context)

        request.session['forgot_password_email'] = email
        return redirect('forgot_password_step2')
    
    context = {}
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    return render(request, 'forgot_password_step1.html', context)

def forgot_password_step2(request):
    """Forgot Password Step 2: Verify OTP"""
    if not request.session.get('forgot_password_email'):
        return redirect('forgot_password_step1')
    
    email = request.session.get('forgot_password_email')
    
    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'resend_otp':
            try:
                otp_code = create_otp(email, 'forgot_password')
                email_sent = EmailService.send_otp_email(email, otp_code)
                if not email_sent:
                    context = {
                        'error': 'Không thể gửi lại mã OTP. Vui lòng thử lại sau.',
                        'email': email
                    }
                    context.update(_get_notification_context(request))
                    context.update(_get_user_role_context(request))
                    return render(request, 'forgot_password_step2.html', context)

                context = {
                    'email': email,
                    'success': 'Mã OTP mới đã được gửi đến email của bạn.'
                }
                context.update(_get_notification_context(request))
                context.update(_get_user_role_context(request))
                return render(request, 'forgot_password_step2.html', context)
            except Exception:
                context = {
                    'error': 'Có lỗi xảy ra khi gửi lại mã OTP.',
                    'email': email
                }
                context.update(_get_notification_context(request))
                context.update(_get_user_role_context(request))
                return render(request, 'forgot_password_step2.html', context)

        otp_code = request.POST.get('otp_code', '').strip()
        if not otp_code:
            context = {'error': 'Vui lòng nhập mã OTP', 'email': email}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_step2.html', context)

        if not verify_otp(email, otp_code, 'forgot_password'):
            context = {'error': 'Mã OTP không hợp lệ hoặc đã hết hạn', 'email': email}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_step2.html', context)

        request.session['forgot_password_verified'] = True
        return redirect('forgot_password_step3')

    context = {'email': email}
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    return render(request, 'forgot_password_step2.html', context)


def forgot_password_step3(request):
    """Forgot Password Step 3: Reset password"""
    if not request.session.get('forgot_password_email'):
        return redirect('forgot_password_step1')
    if not request.session.get('forgot_password_verified'):
        return redirect('forgot_password_step2')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        errors = {}

        if not password:
            errors['password'] = "Vui lòng nhập mật khẩu"
        else:
            valid, message = ValidationUtils.validate_password_strength(password)
            if not valid:
                errors['password'] = message

        if password != password_confirm:
            errors['password_confirm'] = "Mật khẩu xác nhận không khớp"

        if not errors:
            email = request.session.get('forgot_password_email')
            user = User.objects.get(email__iexact=email)
            user.set_password(password)
            user.save()

            del request.session['forgot_password_email']
            if 'forgot_password_verified' in request.session:
                del request.session['forgot_password_verified']

            context = {}
            context.update(_get_notification_context(request))
            context.update(_get_user_role_context(request))
            return render(request, 'forgot_password_success.html', context)

        context = {'errors': errors}
        context.update(_get_notification_context(request))
        context.update(_get_user_role_context(request))
        return render(request, 'forgot_password_step3.html', context)

    context = {}
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    return render(request, 'forgot_password_step3.html', context)

# ========== POST MANAGEMENT ==========

@login_required(login_url='forum')
@require_POST
def create_post(request):
    """Create new post - handles form submission from forum popup"""
    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()
    category_id = request.POST.get('category')
    privacy = request.POST.get('privacy', 'public')
    images = request.FILES.getlist('images')
    image_url = request.POST.get('image_url', '').strip()
    image_urls = [url.strip() for url in request.POST.getlist('image_urls') if url.strip()]
    
    errors = {}
    
    if not title:
        errors['title'] = "Vui lòng nhập tiêu đề"
    if not content:
        errors['content'] = "Vui lòng nhập nội dung"
    if not category_id:
        errors['category'] = "Vui lòng chọn danh mục"
    
    # Check AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not errors:
        try:
            category = get_object_or_404(Category, id=category_id)

            uploaded_urls = []
            if images:
                uploaded_urls = _upload_post_images_to_cloudinary(images, request.user.id)
            elif image_urls:
                uploaded_urls = image_urls
            elif image_url:
                uploaded_urls = [image_url]
            
            post = Post.objects.create(
                title=title,
                content=content,
                category=category,
                author=request.user,
                privacy=privacy,
                image=uploaded_urls[0] if uploaded_urls else None
            )

            for idx, uploaded_url in enumerate(uploaded_urls):
                PostImage.objects.create(post=post, image=uploaded_url, order=idx)
            # Create notification for followers
            Notification.objects.create(
                recipient=request.user,
                notification_type='system',
                title='Bài viết của bạn',
                message=f'Bài viết "{post.title}" đã được đăng thành công',
                post=post
            )
            
            # Return JSON for AJAX requests
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Bài viết đã được đăng thành công!', 'post_id': post.id})
            
            return redirect('post_detail', post_id=post.id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Có lỗi xảy ra: {str(e)}"
            errors['general'] = error_msg
    
    # Return JSON error for AJAX requests
    if is_ajax:
        return JsonResponse({'success': False, 'errors': errors}, status=400)
    
    # For non-AJAX POST, redirect to forum with error
    return redirect('forum')

@login_required(login_url='forum')
def edit_post(request, post_id):
    """Edit post"""
    post = get_object_or_404(Post, id=post_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if post.author != request.user:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền chỉnh sửa bài viết này'}, status=403)
        return HttpResponseForbidden("Bạn không có quyền chỉnh sửa bài viết này")

    # Edit UI is handled in popup modal; disable standalone edit page.
    if request.method != 'POST':
        return redirect('forum')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category_id = request.POST.get('category')
        privacy = request.POST.get('privacy', 'public')
        images = request.FILES.getlist('images')
        image_url = request.POST.get('image_url', '').strip()
        image_urls = [url.strip() for url in request.POST.getlist('image_urls') if url.strip()]
        
        errors = {}
        
        if not title:
            errors['title'] = "Vui lòng nhập tiêu đề"
        if not content:
            errors['content'] = "Vui lòng nhập nội dung"
        # Only require category if it's a full form edit (not AJAX popup)
        if not category_id and not is_ajax:
            errors['category'] = "Vui lòng chọn danh mục"
        
        if not errors:
            try:
                # For AJAX requests, use existing category; for full form, get provided category
                if is_ajax:
                    category = post.category
                else:
                    category = get_object_or_404(Category, id=category_id)
                
                post.title = title
                post.content = content
                post.category = category
                post.privacy = privacy

                uploaded_urls = []
                if images:
                    uploaded_urls = _upload_post_images_to_cloudinary(images, request.user.id)
                elif image_urls:
                    uploaded_urls = image_urls
                elif image_url:
                    uploaded_urls = [image_url]

                if uploaded_urls:
                    post.images.all().delete()
                    for idx, uploaded_url in enumerate(uploaded_urls):
                        PostImage.objects.create(post=post, image=uploaded_url, order=idx)
                    post.image = uploaded_urls[0]
                
                post.save()
                
                # Create notification for user
                Notification.objects.create(
                    recipient=request.user,
                    notification_type='post_edited',
                    title='Bài viết được chỉnh sửa',
                    message=f'Bài viết "{post.title}" đã được cập nhật thành công',
                    post=post
                )
                
                # Return JSON for AJAX requests
                if is_ajax:
                    return JsonResponse({'success': True, 'message': 'Bài viết đã được cập nhật'})
                return redirect('post_detail', post_id=post.id)
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_msg = f"Có lỗi xảy ra khi cập nhật bài viết: {str(e)}"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg}, status=500)
                errors['general'] = error_msg
        
        if is_ajax and errors:
            return JsonResponse({'success': False, 'error': ', '.join(errors.values())}, status=400)

        return redirect('forum')

    return redirect('forum')

@login_required(login_url='forum')
@require_POST
def delete_post(request, post_id):
    """Delete post"""
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user and not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền xóa bài viết này'}, status=403)
        return HttpResponseForbidden("Bạn không có quyền xóa bài viết này")
    
    post.delete()
    
    # Check AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({'success': True, 'message': 'Bài viết đã được xóa'})

    next_url = (request.POST.get('next') or '').strip()
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    
    return redirect('forum')

def post_detail(request, post_id):
    """View post detail"""
    post = get_object_or_404(
        Post.objects.select_related('category', 'author', 'verified_by').prefetch_related(
            'likes', 'images', 'comments__author', 'comments__likes', 'verifications__doctor'
        ),
        id=post_id
    )
    comments = post.comments.select_related('author', 'verified_by', 'parent').prefetch_related('likes')
    role_context = _get_user_role_context(request)
    can_view_anonymous_identity = role_context.get('can_verify_posts', False)
    
    context = {
        'post': post,
        'comments': comments,
        'is_author': request.user == post.author if request.user.is_authenticated else False,
        'user_liked': request.user in post.likes.all() if request.user.is_authenticated else False,
        'can_view_anonymous_identity': can_view_anonymous_identity,
    }
    context.update(_get_notification_context(request))
    context.update(role_context)
    return render(request, 'post_detail.html', context)


def _serialize_comment(comment, request_user=None, can_view_anonymous_identity=False):
    user_id = request_user.id if request_user and request_user.is_authenticated else None
    can_manage = bool(user_id and (comment.author_id == user_id or (request_user and request_user.is_staff)))
    return {
        'id': comment.id,
        'post_id': comment.post_id,
        'parent_id': comment.parent_id,
        'author': comment.display_author_name(can_view_anonymous_identity),
        'author_username': comment.author.username,
        'content': comment.content,
        'is_anonymous': comment.is_anonymous,
        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
        'updated_at': comment.updated_at.strftime('%d/%m/%Y %H:%M'),
        'likes_count': comment.likes.count(),
        'is_hidden': comment.is_hidden,
        'can_reply': bool(request_user and request_user.is_authenticated),
        'can_edit': can_manage,
        'can_delete': can_manage,
    }

@require_POST
def add_comment(request, post_id):
    """Add comment to post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Vui lòng đăng nhập để bình luận',
            'authenticated': False
        }, status=401)
        
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    is_anonymous = str(request.POST.get('is_anonymous', '')).lower() in {'1', 'true', 'on', 'yes'}
    
    if not content:
        return JsonResponse({'error': 'Nội dung không được để trống'}, status=400)

    parent_comment = None
    if parent_id:
        parent_comment = get_object_or_404(Comment, id=parent_id, post=post, is_hidden=False)
    
    comment = Comment.objects.create(
        post=post,
        author=request.user,
        parent=parent_comment,
        content=content,
        is_anonymous=is_anonymous
    )
    
    actor_name = 'Một người dùng ẩn danh' if is_anonymous else request.user.username

    # Create notification for post author.
    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            notification_type='comment',
            title='Bình luận mới',
            message=f'{actor_name} đã bình luận trên bài viết của bạn',
            post=post,
            comment=comment
        )

    # Create notification for parent comment author if this is a reply.
    if parent_comment and parent_comment.author != request.user and parent_comment.author != post.author:
        Notification.objects.create(
            recipient=parent_comment.author,
            notification_type='comment',
            title='Có phản hồi bình luận',
            message=f'{actor_name} đã trả lời bình luận của bạn',
            post=post,
            comment=comment
        )

    role_context = _get_user_role_context(request)
    can_view_anonymous_identity = role_context.get('can_verify_posts', False)
    
    return JsonResponse({
        'success': True,
        'comment': _serialize_comment(comment, request.user, can_view_anonymous_identity)
    })


@login_required(login_url='forum')
@require_POST
def edit_comment(request, comment_id):
    """Edit an existing comment."""
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền sửa bình luận này'}, status=403)

    content = request.POST.get('content', '').strip()
    is_anonymous = str(request.POST.get('is_anonymous', '')).lower() in {'1', 'true', 'on', 'yes'}
    if not content:
        return JsonResponse({'success': False, 'error': 'Nội dung không được để trống'}, status=400)

    comment.content = content
    comment.is_anonymous = is_anonymous
    comment.save(update_fields=['content', 'is_anonymous', 'updated_at'])

    role_context = _get_user_role_context(request)
    can_view_anonymous_identity = role_context.get('can_verify_posts', False)
    return JsonResponse({'success': True, 'comment': _serialize_comment(comment, request.user, can_view_anonymous_identity)})

@login_required(login_url='forum')
@require_POST
def delete_comment(request, comment_id):
    """Delete comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền xóa bình luận này'}, status=403)
    
    deleted_comment_id = comment.id
    comment.delete()
    return JsonResponse({'success': True, 'deleted_comment_id': deleted_comment_id})

# ========== REPORTING SYSTEM ==========

@login_required(login_url='forum')
def create_report(request):
    """Create report for violation"""
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        # Disable comment reports: only report posts.
        comment_id = None
        report_type = request.POST.get('report_type')
        reason = request.POST.get('reason', '')
        
        errors = {}
        
        if not post_id:
            errors['target'] = "Vui lòng chọn nội dung để báo cáo"
        
        if not report_type:
            errors['report_type'] = "Vui lòng chọn loại vi phạm"
        
        if not errors:
            post = None
            
            if post_id:
                post = get_object_or_404(Post, id=post_id)
            
            # Check if already reported
            existing_report = Report.objects.filter(
                reporter=request.user,
                post=post,
                comment__isnull=True,
                is_processed=False
            ).exists()
            
            if existing_report:
                return JsonResponse({
                    'error': 'Bạn đã báo cáo nội dung này rồi'
                }, status=400)
            
            report = Report.objects.create(
                reporter=request.user,
                post=post,
                report_type=report_type,
                reason=reason
            )
            
            # Increase report count
            if post:
                post.report_count += 1
                if post.report_count >= 10:
                    post.is_hidden = True
                post.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cảm ơn bạn đã phản hồi, chúng tôi sẽ xem xét nội dung này'
            })
        
        return JsonResponse({'errors': errors}, status=400)

# ========== NOTIFICATIONS ==========

@login_required(login_url='forum')
def notifications(request):
    """View all notifications"""
    filter_type = request.GET.get('filter', 'all')
    
    notifications_qs = Notification.objects.filter(
        recipient=request.user
    ).select_related(
        'post__author', 'post__category', 'comment__author'
    ).order_by('-created_at')
    
    if filter_type == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)
    
    paginator = Paginator(notifications_qs, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'notifications': page_obj,
        'filter_type': filter_type,
        'total_unread': Notification.objects.filter(recipient=request.user, is_read=False).count()
    }
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    
    return render(request, 'notifications.html', context)

@login_required(login_url='forum')
def notification_detail(request, notification_id):
    """View notification detail"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    context = {
        'notification': notification
    }
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    return render(request, 'notification_detail.html', context)

@login_required(login_url='forum')
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    return JsonResponse({'success': True})

@login_required(login_url='forum')
@require_http_methods(["POST"])
def edit_notification(request, notification_id):
    """Notification editing is disabled for end users."""
    return JsonResponse({'error': 'Thông báo chỉ hỗ trợ xem và xóa'}, status=403)


@login_required(login_url='forum')
def personal_info(request):
    """Personal info page with navbar notification context."""
    if not request.user.is_authenticated:
        return redirect('forum')
    
    context = {
        'target_user': request.user,
        'user_profile': UserProfile.objects.get_or_create(user=request.user)[0],
    }
    context.update(_get_notification_context(request))
    context.update(_get_user_role_context(request))
    return render(request, 'personal_info.html', context)


@login_required(login_url='forum')
@require_http_methods(["POST"])
def api_update_personal_info(request):
    """Update editable personal information for the logged-in user."""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dữ liệu không hợp lệ'}, status=400)

    full_name = (data.get('full_name') or '').strip()

    if not full_name:
        return JsonResponse({'error': 'Họ và tên không được để trống'}, status=400)

    current_user = request.user
    if 'email' in data and (data.get('email') or '').strip() and (data.get('email') or '').strip() != current_user.email:
        return JsonResponse({'error': 'Email không thể thay đổi'}, status=400)

    name_parts = full_name.split(maxsplit=1)
    current_user.first_name = name_parts[0]
    current_user.last_name = name_parts[1] if len(name_parts) > 1 else ''
    current_user.save(update_fields=['first_name', 'last_name'])

    return JsonResponse({
        'success': True,
        'message': 'Cập nhật thông tin thành công',
        'full_name': current_user.get_full_name() or current_user.username,
        'email': current_user.email,
        'username': current_user.username,
    })


@login_required(login_url='forum')
@require_http_methods(["POST"])
def api_change_password(request):
    """Change password for the logged-in user."""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dữ liệu không hợp lệ'}, status=400)

    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not current_password or not new_password or not confirm_password:
        return JsonResponse({'error': 'Vui lòng nhập đầy đủ thông tin'}, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({'error': 'Mật khẩu hiện tại không đúng'}, status=400)

    if len(new_password) < 8:
        return JsonResponse({'error': 'Mật khẩu mới phải có ít nhất 8 ký tự'}, status=400)

    if new_password != confirm_password:
        return JsonResponse({'error': 'Mật khẩu xác nhận không khớp'}, status=400)

    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)

    return JsonResponse({'success': True, 'message': 'Đổi mật khẩu thành công'})

@login_required(login_url='forum')
@require_POST
def delete_notification(request, notification_id):
    """Delete a single notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.delete()
        return JsonResponse({'success': True, 'message': 'Xóa thông báo thành công'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='forum')
@require_POST
def delete_multiple_notifications(request):
    """Delete multiple notifications"""
    try:
        data = json.loads(request.body) if request.body else {}
        notification_ids = data.get('ids', [])
        
        if not notification_ids:
            return JsonResponse({'error': 'Không chọn thông báo nào'}, status=400)
        
        deleted_count, _ = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Xóa {deleted_count} thông báo thành công',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='forum')
@require_POST
def create_system_notification(request):
    """Create system notification (Admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Chỉ quản trị viên mới có thể tạo thông báo'}, status=403)
    
    try:
        data = json.loads(request.body) if request.body else {}
        title = data.get('title', '').strip()
        message = data.get('message', '').strip()
        user_ids = data.get('user_ids', [])  # List of user IDs, empty = all users
        
        if not title or not message:
            return JsonResponse({'error': 'Tiêu đề và nội dung không được để trống'}, status=400)
        
        if user_ids:
            # Send to specific users
            users = User.objects.filter(id__in=user_ids)
        else:
            # Send to all users
            users = User.objects.filter(is_active=True)
        
        notifications = []
        for user in users:
            notification = Notification.objects.create(
                recipient=user,
                notification_type='system',
                title=title,
                message=message
            )
            notifications.append(notification.id)
        
        return JsonResponse({
            'success': True,
            'message': f'Đã gửi thông báo đến {len(notifications)} người dùng',
            'notification_ids': notifications
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ========== EXPERT VERIFICATION ==========

@login_required(login_url='forum')
def verify_post(request, post_id):
    """Create or update verification for a post by current doctor."""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is verified doctor
    try:
        profile = request.user.profile
        if profile.user_type != 'doctor' or not profile.is_verified_doctor:
            return HttpResponseForbidden("Chỉ bác sĩ xác minh mới có thể kiểm duyệt bài viết")
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden("Chỉ bác sĩ xác minh mới có thể kiểm duyệt bài viết")
    
    if request.method != 'POST':
        return redirect('post_detail', post_id=post.id)

    verification_reasons = request.POST.getlist('verification_reasons')
    fallback_reason = request.POST.get('verification_reason', '').strip()
    if fallback_reason:
        verification_reasons.append(fallback_reason)

    valid_reason_codes = {code for code, _ in Post.VERIFICATION_REASONS}
    normalized_reasons = []
    for code in verification_reasons:
        code = (code or '').strip()
        if code and code in valid_reason_codes and code not in normalized_reasons:
            normalized_reasons.append(code)

    raw_custom_reasons = request.POST.get('custom_reasons', '').strip()
    custom_reasons = []
    if raw_custom_reasons:
        for line in raw_custom_reasons.splitlines():
            chunks = [part.strip() for part in line.split(',') if part.strip()]
            for chunk in chunks:
                if chunk not in custom_reasons:
                    custom_reasons.append(chunk)

    verification_note = request.POST.get('verification_note', '').strip()

    if not normalized_reasons and not custom_reasons:
        return JsonResponse({'error': 'Vui lòng chọn hoặc nhập ít nhất một lý do kiểm duyệt'}, status=400)

    verification_id = request.POST.get('verification_id')
    record = None
    if verification_id:
        record = PostVerification.objects.filter(id=verification_id, post=post).first()
        if not record:
            return JsonResponse({'error': 'Không tìm thấy bản kiểm duyệt để chỉnh sửa'}, status=404)
        if not request.user.is_staff and record.doctor_id != request.user.id:
            return JsonResponse({'error': 'Bạn không có quyền chỉnh sửa kiểm duyệt này'}, status=403)

    if record is None:
        record, created = PostVerification.objects.get_or_create(
            post=post,
            doctor=request.user,
            defaults={
                'verification_reasons': ','.join(normalized_reasons),
                'custom_reasons': '\n'.join(custom_reasons),
                'verification_note': verification_note,
                'verified_at': timezone.now(),
            }
        )
        if not created:
            record.verification_reasons = ','.join(normalized_reasons)
            record.custom_reasons = '\n'.join(custom_reasons)
            record.verification_note = verification_note
            record.verified_at = timezone.now()
            record.save(update_fields=['verification_reasons', 'custom_reasons', 'verification_note', 'verified_at', 'updated_at'])
    else:
        record.verification_reasons = ','.join(normalized_reasons)
        record.custom_reasons = '\n'.join(custom_reasons)
        record.verification_note = verification_note
        record.verified_at = timezone.now()
        record.save(update_fields=['verification_reasons', 'custom_reasons', 'verification_note', 'verified_at', 'updated_at'])

    post.refresh_verification_status(save=True)

    Notification.objects.create(
        recipient=post.author,
        notification_type='verified',
        title='Bài viết được kiểm duyệt',
        message='Bài viết của bạn đã được bác sĩ kiểm duyệt',
        post=post
    )

    return JsonResponse({'success': True})

@login_required(login_url='forum')
@require_POST
def unverify_post(request, post_id):
    """Remove one verification record (or current doctor's record)."""
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is doctor/admin
    try:
        profile = request.user.profile
        if profile.user_type != 'doctor' and not request.user.is_staff:
            return HttpResponseForbidden("Chỉ bác sĩ mới có thể gỡ kiểm duyệt")
    except UserProfile.DoesNotExist:
        if not request.user.is_staff:
            return HttpResponseForbidden("Chỉ bác sĩ mới có thể gỡ kiểm duyệt")

    verification_id = request.POST.get('verification_id')
    if verification_id:
        record = PostVerification.objects.filter(id=verification_id, post=post).first()
        if not record:
            return JsonResponse({'error': 'Không tìm thấy bản kiểm duyệt'}, status=404)
        if not request.user.is_staff and record.doctor_id != request.user.id:
            return JsonResponse({'error': 'Bạn không có quyền xóa kiểm duyệt này'}, status=403)
        record.delete()
    else:
        queryset = PostVerification.objects.filter(post=post)
        if not request.user.is_staff:
            queryset = queryset.filter(doctor=request.user)
        deleted_count, _ = queryset.delete()
        if deleted_count == 0:
            return JsonResponse({'error': 'Không có bản kiểm duyệt để gỡ'}, status=404)

    post.refresh_verification_status(save=True)
    
    return JsonResponse({'success': True})


def post_verification_history(request, post_id):
    """Return verification summary + all doctor verification records for popup."""
    post = get_object_or_404(Post.objects.select_related('author'), id=post_id)

    verifications = []
    for record in post.verifications.select_related('doctor').order_by('-verified_at'):
        can_edit = request.user.is_authenticated and (request.user.is_staff or record.doctor_id == request.user.id)
        verifications.append({
            'id': record.id,
            'doctor_name': record.doctor.get_full_name() or record.doctor.username,
            'doctor_username': record.doctor.username,
            'verified_at': record.verified_at.strftime('%d/%m/%Y %H:%M') if record.verified_at else '',
            'verified_relative': timezone.localtime(record.verified_at).strftime('%H:%M %d/%m/%Y') if record.verified_at else '',
            'reason_codes': record.reason_codes,
            'reason_labels': record.reason_labels,
            'custom_reasons': record.custom_reason_items,
            'reason_labels_full': record.all_reason_labels,
            'verification_note': record.verification_note,
            'can_edit': can_edit,
            'is_mine': record.doctor_id == request.user.id,
        })

    can_verify = False
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            can_verify = profile.user_type == 'doctor' and profile.is_verified_doctor
        except UserProfile.DoesNotExist:
            can_verify = False

    return JsonResponse({
        'success': True,
        'post': {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'is_verified': bool(verifications),
            'verified_count': len(verifications),
            'verified_at': post.verified_at.strftime('%d/%m/%Y %H:%M') if post.verified_at else '',
        },
        'verifications': verifications,
        'can_verify': can_verify,
    })

# ========== FORUM VIEWS ==========

def _get_user_role_context(request):
    """Return role flags for current user."""
    context = {
        'is_logged_in': request.user.is_authenticated,
        'is_admin_user': False,
        'is_staff_user': False,
        'is_superuser_user': False,
        'is_doctor_user': False,
        'can_verify_posts': False,
    }

    if not request.user.is_authenticated:
        return context

    context['is_staff_user'] = bool(request.user.is_staff)
    context['is_superuser_user'] = bool(request.user.is_superuser)
    context['is_admin_user'] = bool(request.user.is_staff or request.user.is_superuser)

    try:
        profile = request.user.profile
        context['is_doctor_user'] = profile.user_type == 'doctor'
        context['can_verify_posts'] = (
            profile.user_type == 'doctor' and profile.is_verified_doctor
        )
    except UserProfile.DoesNotExist:
        pass

    return context


def _get_notification_context(request):
    """Return unread count and latest notifications for navbar popup."""
    if not request.user.is_authenticated:
        return {
            'unread_count': 0,
            'recent_notifications': [],
        }

    return {
        'unread_count': Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count(),
        'recent_notifications': Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:10],
    }

def forum_home(request):
    """
    View cho trang chủ Diễn đàn: Hiển thị danh sách Categories và Posts.
    Hỗ trợ tìm kiếm và lọc theo danh mục.
    """
    categories = Category.objects.all()
    posts = Post.objects.filter(is_hidden=False).select_related(
        'category', 'author', 'verified_by'
    ).prefetch_related(
        'likes', 'images', 'comments', 'reports', 'verifications__doctor'
    ).order_by('-created_at')
    
    # Lọc theo danh mục
    category_id = request.GET.get('category')
    if category_id:
        posts = posts.filter(category_id=category_id)
    
    # Tìm kiếm theo từ khóa
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )

    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        posts = posts.filter(created_at__date__gte=date_from)
    if date_to:
        posts = posts.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(posts, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    
    notification_context = _get_notification_context(request)
    role_context = _get_user_role_context(request)
    
    context = {
        'categories': categories,
        'posts': page_obj,
        'selected_category': category_id,
        'search_query': query,
        'base_querystring': query_params.urlencode(),
        'date_from': date_from,
        'date_to': date_to,
    }
    context.update(notification_context)
    context.update(role_context)
    return render(request, 'forum.html', context)

def user_profile(request, username=None):
    """
    View cho trang cá nhân người dùng.
    """
    if username:
        target_user = get_object_or_404(User, username__iexact=username)
    else:
        if not request.user.is_authenticated:
            return redirect('forum')
        target_user = request.user
    
    # Filter posts: exclude anonymous posts unless viewing own profile
    posts_query = Post.objects.filter(
        author=target_user, is_hidden=False
    ).select_related(
        'category', 'author', 'verified_by'
    ).prefetch_related(
        'likes', 'images', 'comments', 'verifications__doctor'
    )
    
    # Exclude anonymous posts if viewing someone else's profile
    is_own_profile = request.user.is_authenticated and request.user == target_user
    if not is_own_profile:
        posts_query = posts_query.exclude(privacy='anonymous')
    
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        posts_query = posts_query.filter(created_at__date__gte=date_from)
    if date_to:
        posts_query = posts_query.filter(created_at__date__lte=date_to)

    posts = posts_query.order_by('-created_at')
    user_profile = UserProfile.objects.get_or_create(user=target_user)[0]
    doctor_title_clean = (user_profile.doctor_title or '').strip()
    for prefix in ('BS.CKII.', 'BS.CKII'):
        if doctor_title_clean.upper().startswith(prefix):
            doctor_title_clean = doctor_title_clean[len(prefix):].strip()
            break
    # Hide "khoa" token in doctor profile title for cleaner display.
    doctor_title_clean = re.sub(r'\bkhoa\b', '', doctor_title_clean, flags=re.IGNORECASE)
    doctor_title_clean = re.sub(r'\s+', ' ', doctor_title_clean).strip(' -,:;')
    
    # Count statistics
    total_likes = sum(post.likes.count() for post in posts)
    total_comments = sum(post.comments.count() for post in posts)
    verified_posts = posts.filter(verified_by_expert=True).count()
    
    notification_context = _get_notification_context(request)
    role_context = _get_user_role_context(request)
    
    context = {
        'posts': posts,
        'post_count': posts.count(),
        'target_user': target_user,
        'user_profile': user_profile,
        'doctor_title_clean': doctor_title_clean,
        'is_own_profile': is_own_profile,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'verified_posts': verified_posts,
        'categories': Category.objects.all(),
        'date_from': date_from,
        'date_to': date_to,
    }
    context.update(notification_context)
    context.update(role_context)
    return render(request, 'profile.html', context)

def landing_page(request):
    """
    View cho trang Landing: Hiển thị một vài bài viết nổi bật (nhiều likes nhất).
    """
    # Get statistics
    total_users = User.objects.count()
    total_doctors = UserProfile.objects.filter(user_type='doctor').count()
    total_posts = Post.objects.filter(is_hidden=False).count()

    topics = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__is_hidden=False))
    ).order_by('-post_count', '-created_at')[:6]

    notification_context = _get_notification_context(request)
    role_context = _get_user_role_context(request)
    
    context = {
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_posts': total_posts,
        'topics': topics,
    }
    context.update(notification_context)
    context.update(role_context)
    return render(request, 'landing.html', context)

# ========== ADMIN VIEWS ==========

def admin_login_required(view_func):
    """Decorator: Yêu cầu login + is_staff để vào admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=/admin/')
        if not request.user.is_staff:
            return HttpResponseForbidden("❌ Bạn không có quyền vào admin panel")
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login(request):
    """Admin Login Page"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        if request.user.is_staff:
            return redirect('/admin-panel/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('/admin/')
            if user.is_staff:
                login(request, user)
                return redirect('/admin-panel/')
            else:
                error = "❌ Tài khoản không có quyền admin"
        else:
            error = "❌ Username hoặc password không đúng"
        
        return render(request, 'admin_login.html', {'error': error, 'username': username})
    
    return render(request, 'admin_login.html', {})


def custom_404(request, invalid_path=None, exception=None):
    return render(request, '404.html', status=404)

@admin_login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    stats = {
        'total_users': User.objects.count(),
        'total_categories': Category.objects.count(),
        'total_reports': Report.objects.count(),
    }
    return render(request, 'admin_dashboard.html', stats)

@admin_login_required
def admin_posts(request):
    """Admin Posts Management"""
    posts = Post.objects.select_related('author', 'category', 'verified_by').order_by('-created_at')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        posts = posts.filter(created_at__date__gte=date_from)
    if date_to:
        posts = posts.filter(created_at__date__lte=date_to)

    context = {
        'posts': posts,
        'total_posts': posts.count(),
        'verified_posts': posts.filter(verified_by_expert=True).count(),
        'hidden_posts': posts.filter(is_hidden=True).count(),
        'unverified_count': posts.filter(verified_by_expert=False).count(),
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_posts.html', context)

@admin_login_required
def admin_categories(request):
    """Admin Categories Management"""
    categories = Category.objects.annotate(post_count=Count('posts')).order_by('-created_at')
    total_posts = sum(cat.post_count for cat in categories)
    context = {
        'categories': categories,
        'total_categories': categories.count(),
        'total_posts': total_posts,
    }
    return render(request, 'admin_categories.html', context)

@admin_login_required
def admin_accounts(request):
    """Admin Accounts Management"""
    users = User.objects.select_related('profile').order_by('-date_joined')
    user_profiles = UserProfile.objects.select_related('user')
    context = {
        'users': users,
        'user_profiles': {up.user_id: up for up in user_profiles},
        'total_users': users.count(),
        'doctors': users.filter(profile__user_type='doctor').count(),
        'admins': users.filter(is_staff=True).count(),
    }
    return render(request, 'admin_accounts.html', context)

@admin_login_required
def admin_reports(request):
    """Admin Reports Management"""
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if status_filter == 'processed':
        reports = Report.objects.select_related('reporter', 'post', 'comment', 'processed_by').filter(
            is_processed=True,
            post__isnull=False,
            comment__isnull=True,
        ).order_by('-processed_at')
    elif status_filter == 'unprocessed':
        reports = Report.objects.select_related('reporter', 'post', 'comment', 'processed_by').filter(
            is_processed=False,
            post__isnull=False,
            comment__isnull=True,
        ).order_by('-created_at')
    else:
        reports = Report.objects.select_related('reporter', 'post', 'comment', 'processed_by').filter(
            post__isnull=False,
            comment__isnull=True,
        ).order_by('-created_at')

    if date_from:
        reports = reports.filter(created_at__date__gte=date_from)
    if date_to:
        reports = reports.filter(created_at__date__lte=date_to)
    
    grouped_reports_map = {}
    for report in reports:
        if not report.post_id:
            continue

        bucket = grouped_reports_map.get(report.post_id)
        if bucket is None:
            bucket = {
                'post': report.post,
                'report_id': report.id,
                'report_count': 0,
                'latest_created_at': report.created_at,
                'is_processed': report.is_processed,
                'details': [],
                'reporters_seen': set(),
                'reason_seen': set(),
            }
            grouped_reports_map[report.post_id] = bucket

        bucket['report_count'] += 1
        if report.created_at > bucket['latest_created_at']:
            bucket['latest_created_at'] = report.created_at

        reporter_name = report.reporter.get_full_name() or report.reporter.username
        if reporter_name not in bucket['reporters_seen']:
            bucket['reporters_seen'].add(reporter_name)

        reason_text = report.get_report_type_display()
        if (report.reason or '').strip():
            reason_text = f"{reason_text}: {report.reason.strip()}"
        if reason_text not in bucket['reason_seen']:
            bucket['reason_seen'].add(reason_text)

        bucket['details'].append({
            'id': report.id,
            'reporter_name': reporter_name,
            'report_type': report.get_report_type_display(),
            'reason': (report.reason or '').strip(),
            'created_at': report.created_at,
        })

    grouped_reports = []
    for _, row in grouped_reports_map.items():
        row.pop('reporters_seen', None)
        row.pop('reason_seen', None)
        grouped_reports.append(row)

    grouped_reports.sort(key=lambda row: (row['report_count'], row['latest_created_at']), reverse=True)

    context = {
        'reports': grouped_reports,
        'total_reports': Report.objects.count(),
        'unprocessed_count': Report.objects.filter(is_processed=False).count(),
        'processed_count': Report.objects.filter(is_processed=True).count(),
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_reports.html', context)

@admin_login_required
@require_POST
def process_report(request, report_id):
    """Process report"""
    report = get_object_or_404(Report, id=report_id)
    action = request.POST.get('action')  # 'approve' or 'reject' or 'delete_post'
    
    report.is_processed = True
    report.processed_by = request.user
    report.processed_at = timezone.now()
    report.save()

    # If admin approves violation, hide reported content.
    if action == 'approve':
        if report.post:
            report.post.is_hidden = True
            report.post.save(update_fields=['is_hidden'])
        if report.comment:
            report.comment.is_hidden = True
            report.comment.save(update_fields=['is_hidden'])
    elif action == 'delete_post' and report.post:
        report.post.delete()
    
    # Create notification for reporter
    message = "Báo cáo của bạn đã được xử lý"
    if action == 'approve':
        message += " - nội dung vi phạm đã bị xóa/ẩn"
    elif action == 'delete_post':
        message += " - bài viết đã bị xóa"
    
    Notification.objects.create(
        recipient=report.reporter,
        notification_type='report_processed',
        title='Báo cáo được xử lý',
        message=message
    )
    
    return redirect('admin_reports')

@admin_login_required
def admin_notifications(request):
    """Admin Notifications Management"""
    notifications = Notification.objects.select_related('recipient', 'post', 'comment').order_by('-created_at')
    
    # Count statistics
    system_notifications = notifications.filter(notification_type='system')
    read_count = notifications.filter(is_read=True).count()
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications[:100],  # Show recent notifications
        'total_notifications': notifications.count(),
        'system_notifications_count': system_notifications.count(),
        'read_count': read_count,
        'unread_count': unread_count,
    }
    return render(request, 'admin_notifications.html', context)

# ========== ENHANCED ADMIN FUNCTIONS ==========

@admin_login_required
def admin_user_management(request):
    """Advanced user management"""
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # Search & filter
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', 'all')  # all, doctors, admins
    
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query) | 
            Q(first_name__icontains=query)
        )
    
    if filter_type == 'doctors':
        users = users.filter(profile__user_type='doctor')
    elif filter_type == 'admins':
        users = users.filter(is_staff=True)
    
    # Paginate
    paginator = Paginator(users, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'users': page_obj,
        'query': query,
        'filter_type': filter_type,
        'total_users': User.objects.count(),
        'doctors': User.objects.filter(profile__user_type='doctor').count(),
    }
    return render(request, 'admin_user_management.html', context)

@admin_login_required
@require_POST
def admin_change_user_role(request, user_id):
    """Change user role"""
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    
    try:
        data = json.loads(request.body) if request.body else {}
        new_role = data.get('user_type')
        
        if new_role not in ['user', 'doctor', 'admin']:
            return JsonResponse({'error': 'Invalid role'}, status=400)
        
        old_role = profile.user_type
        profile.user_type = new_role
        if new_role == 'doctor':
            profile.is_verified_doctor = True
        else:
            profile.is_verified_doctor = False
            
        profile.save()
        
        if not user.is_active:
            user.is_active = True
            user.save()
        
        user.is_staff = (new_role == 'admin')
        user.save(update_fields=['is_active', 'is_staff'])
        
        # Log action
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_role_change',
            action_description=f'Changed {user.username} role from {old_role} to {new_role}',
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Changed role for {user.username}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@admin_login_required
@require_POST
def admin_delete_user(request, user_id):
    """Delete user account"""
    user = get_object_or_404(User, id=user_id)
    
    if user.is_staff:
        return JsonResponse({'error': 'Không thể xóa quản trị viên'}, status=403)
    
    try:
        username = user.username
        user.delete()
        
        # Log action
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_delete',
            action_description=f'Deleted user account: {username}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} đã bị xóa'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@admin_login_required
def admin_moderation(request):
    """Advanced post/comment moderation"""
    filter_type = request.GET.get('filter', 'pending')  # pending, reported, hidden, all
    
    posts = Post.objects.select_related('author', 'category', 'verified_by').all()
    
    if filter_type == 'pending':
        posts = posts.filter(verified_by_expert=False)
    elif filter_type == 'reported':
        posts = posts.filter(report_count__gt=0)
    elif filter_type == 'hidden':
        posts = posts.filter(is_hidden=True)
    
    # Search
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    
    posts = posts.order_by('-created_at')[:100]
    
    context = {
        'posts': posts,
        'filter_type': filter_type,
        'total_pending': Post.objects.filter(verified_by_expert=False).count(),
        'total_reported': Post.objects.filter(report_count__gt=0).count(),
        'total_hidden': Post.objects.filter(is_hidden=True).count(),
    }
    return render(request, 'admin_moderation.html', context)

@admin_login_required
@require_POST
def admin_bulk_post_action(request):
    """Bulk actions on posts"""
    try:
        data = json.loads(request.body) if request.body else {}
        post_ids = data.get('post_ids', [])
        action = data.get('action')
        
        if not post_ids or not action:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        posts = Post.objects.filter(id__in=post_ids)
        count = 0
        
        if action == 'hide':
            posts.update(is_hidden=True)
            count = posts.count()
            action_type = 'post_hide'
            desc = f'Hidden {count} posts'
        elif action == 'unhide':
            posts.update(is_hidden=False)
            count = posts.count()
            action_type = 'post_hide'
            desc = f'Unhide {count} posts'
        elif action == 'delete':
            count = posts.count()
            posts.delete()
            action_type = 'post_delete'
            desc = f'Deleted {count} posts'
        elif action == 'verify':
            count = posts.count()
            now = timezone.now()
            for post in posts:
                PostVerification.objects.update_or_create(
                    post=post,
                    doctor=request.user,
                    defaults={
                        'verification_reasons': post.verification_reasons or post.verification_reason or 'expert',
                        'verification_note': post.verification_note or '',
                        'verified_at': now,
                    }
                )
                post.refresh_verification_status(save=True)
            action_type = 'post_verify'
            desc = f'Verified {count} posts'
        elif action == 'unverify':
            count = posts.count()
            for post in posts:
                PostVerification.objects.filter(post=post).delete()
                post.refresh_verification_status(save=True)
            action_type = 'post_verify'
            desc = f'Removed verification from {count} posts'
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # Log action
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type=action_type,
            action_description=desc,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{desc.capitalize()}',
            'count': count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@admin_login_required
def admin_settings(request):
    """System settings management"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            changes = []
            
            for key, value in data.items():
                if key.startswith('_'):
                    continue
                
                setting, created = SystemSettings.objects.get_or_create(key=key)
                old_value = setting.value
                
                # Convert checkbox values to strings
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                
                setting.value = str(value)
                setting.updated_by = request.user
                setting.save()
                
                changes.append(f'{key}: {old_value} → {value}')
            
            # Log action
            AdminActivityLog.objects.create(
                admin=request.user,
                action_type='settings_update',
                action_description=f'Updated settings: {", ".join(changes) if changes else "no changes"}',
                ip_address=request.META.get('REMOTE_ADDR'),
                status='success'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Đã cập nhật {len(changes)} cài đặt'
            })
        except Exception as e:
            AdminActivityLog.objects.create(
                admin=request.user,
                action_type='settings_update',
                action_description=f'Failed to update settings',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR'),
                status='failed'
            )
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET: Retrieve all settings
    settings = SystemSettings.objects.all()
    settings_dict = {}
    
    # Default settings
    defaults = {
        'report_threshold': '5',
        'max_posts_per_day': '10',
        'maintenance_mode': 'false',
        'max_comments_per_hour': '30',
        'min_followers_for_expert': '10',
        'require_email_verification': 'false',
        'email_notifications_enabled': 'true',
        'daily_admin_digest': 'true',
        'digest_send_time': '09:00',
        'public_api_enabled': 'false',
        'api_rate_limit': '60',
        'app_name': 'MomCare',
        'support_email': 'support@momcare.com',
        'announcement_banner': ''
    }
    
    # Merge with database settings
    for key, default_value in defaults.items():
        setting = settings.filter(key=key).first()
        if setting:
            settings_dict[key] = setting.value
        else:
            settings_dict[key] = default_value
    
    context = {
        'settings': settings_dict,
    }
    return render(request, 'admin_settings.html', context)

@admin_login_required
def admin_activity_logs(request):
    """View admin activity logs"""
    logs = AdminActivityLog.objects.select_related('admin', 'target_user', 'target_post', 'target_comment').order_by('-created_at')
    
    # Build filter dict
    filters = {
        'action_type': request.GET.get('action_type', ''),
        'admin_id': request.GET.get('admin_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    
    # Filter
    if filters['action_type']:
        logs = logs.filter(action_type=filters['action_type'])
    if filters['admin_id']:
        logs = logs.filter(admin_id=filters['admin_id'])
    if filters['date_from']:
        logs = logs.filter(created_at__date__gte=filters['date_from'])
    if filters['date_to']:
        logs = logs.filter(created_at__date__lte=filters['date_to'])
    
    # Paginate
    paginator = Paginator(logs, 50)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filters': filters,
        'admins': User.objects.filter(is_staff=True).order_by('first_name'),
    }
    return render(request, 'admin_activity_logs.html', context)

@admin_login_required
def admin_advanced_dashboard(request):
    """Advanced dashboard with more statistics"""
    from django.db.models import Count, Q
    from datetime import timedelta
    
    # Get statistics
    now = timezone.now()
    today = now.date()
    this_week = now - timedelta(days=7)
    this_month = now - timedelta(days=30)
    
    stats = {
        'total_users': User.objects.count(),
        'total_posts': Post.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_reports': Report.objects.count(),
        
        'today_posts': Post.objects.filter(created_at__date=today).count(),
        'today_comments': Comment.objects.filter(created_at__date=today).count(),
        'today_reports': Report.objects.filter(created_at__date=today).count(),
        
        'week_posts': Post.objects.filter(created_at__gte=this_week).count(),
        'week_comments': Comment.objects.filter(created_at__gte=this_week).count(),
        
        'month_posts': Post.objects.filter(created_at__gte=this_month).count(),
        'month_comments': Comment.objects.filter(created_at__gte=this_month).count(),
        
        'pending_reports': Report.objects.filter(is_processed=False).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'hidden_posts': Post.objects.filter(is_hidden=True).count(),
        
        'verified_posts': Post.objects.filter(verified_by_expert=True).count(),
        'doctors': User.objects.filter(profile__user_type='doctor').count(),
    }
    
    # Top posts
    top_posts = Post.objects.annotate(
        comment_count=Count('comments')
    ).order_by('-comment_count')[:5]
    
    # Top users by posts
    top_users = User.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:5]
    
    # Recent activity
    recent_logs = AdminActivityLog.objects.select_related('admin').order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'top_posts': top_posts,
        'top_users': top_users,
        'recent_logs': recent_logs,
    }
    return render(request, 'admin_advanced_dashboard.html', context)

# ========== API ENDPOINTS ==========

@csrf_exempt
def api_login_validate(request):
    """API: Validate login credentials and return user info"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Validate input
    if not username or not password:
        return JsonResponse({
            'success': False, 
            'error': 'Vui lòng nhập tên đăng nhập và mật khẩu'
        })
    
    # Check if username exists
    try:
        db_user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tên đăng nhập không tồn tại'
        })
    
    # Authenticate user with password verification
    if not db_user.is_active:
        return JsonResponse({
            'success': False,
            'error': 'Tài khoản của bạn đã bị khóa'
        })

    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if user.is_active:
            # Set Django session
            login(request, user)
            
            # Get user profile info
            try:
                profile = user.profile
                user_type = profile.user_type
            except:
                user_type = 'user'
            
            return JsonResponse({
                'success': True,
                'username': user.username,
                'is_admin': user.is_staff or user.is_superuser,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'user_type': user_type,
                'full_name': user.get_full_name() or user.username,
                'message': 'Đăng nhập thành công!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Tài khoản của bạn không hoạt động'
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Mật khẩu không chính xác'
        })


@csrf_exempt
@require_POST
def api_register_send_otp(request):
    """API: Send OTP to email for registration"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Validate input
    if not email or not username:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập email và tên đăng nhập'
        })
    
    # Validate email format
    if not validate_email(email):
        return JsonResponse({
            'success': False,
            'error': 'Email không hợp lệ'
        })
    
    # Validate username
    if len(username) < 3:
        return JsonResponse({
            'success': False,
            'error': 'Tên đăng nhập phải có ít nhất 3 ký tự'
        })
    
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({
            'success': False,
            'error': 'Tên đăng nhập đã tồn tại'
        })
    
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({
            'success': False,
            'error': 'Email đã tồn tại'
        })
    
    # Delete old OTP if exists
    OTPToken.objects.filter(email=email, otp_type='register').delete()
    
    # Create and send new OTP
    try:
        otp_code = create_otp(email, 'register')
        
        # Send email notification
        EmailService.send_otp_email(email, otp_code)
        
        response = {
            'success': True,
            'message': f'Mã OTP đã được gửi đến {email}',
            'email': email,
            'username': username
        }
        
        # Include OTP code in response during development for testing
        if settings.DEBUG:
            response['otp_code'] = otp_code
        
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi gửi OTP: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def api_register_verify_otp(request):
    """API: Verify OTP and save to session"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        otp_code = data.get('otp_code', '').strip()
        username = data.get('username', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    if not email or not otp_code:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập email và mã OTP'
        })
    
    # Verify OTP
    valid, message = verify_otp(email, otp_code, 'register')
    
    if not valid:
        return JsonResponse({
            'success': False,
            'error': message
        })
    
    # Store registration data in session
    request.session['register_email'] = email
    request.session['register_username'] = username
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'message': 'Xác minh OTP thành công'
    })


@csrf_exempt
@require_POST
def api_register_resend_otp(request):
    """API: Resend OTP to email"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng cung cấp email'
        })
    
    # Delete old OTP
    OTPToken.objects.filter(email=email, otp_type='register').delete()
    
    # Create and send new OTP
    try:
        otp_code = create_otp(email, 'register')
        EmailService.send_otp_email(email, otp_code)
        
        return JsonResponse({
            'success': True,
            'message': f'Mã OTP mới đã được gửi đến {email}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi gửi lại OTP: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def api_register_complete(request):
    """API: Complete registration after password setup"""
    if not request.session.get('register_email'):
        return JsonResponse({
            'success': False,
            'error': 'Phiên đăng ký không hợp lệ'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Get data from session
    email = request.session.get('register_email')
    username = request.session.get('register_username')
    
    # Validate password
    if not password:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập mật khẩu'
        })
    
    if password != password_confirm:
        return JsonResponse({
            'success': False,
            'error': 'Mật khẩu xác nhận không khớp'
        })
    
    if len(password) < 8:
        return JsonResponse({
            'success': False,
            'error': 'Mật khẩu phải có ít nhất 8 ký tự'
        })
    
    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create user profile
        UserProfile.objects.create(user=user, user_type='user')
        
        # Clear session
        if 'register_email' in request.session:
            del request.session['register_email']
        if 'register_username' in request.session:
            del request.session['register_username']
        
        request.session.modified = True
        
        # Auto login
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Đăng ký thành công! Chào mừng đến MomCare!',
            'username': user.username,
            'full_name': user.get_full_name() or user.username
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi tạo tài khoản: {str(e)}'
        }, status=500)


def check_admin_status(request):
    """API: Check current user authentication status"""
    # If username parameter is provided, check that specific user
    username = request.GET.get('username', '')
    
    if username:
        # Old behavior: check specific user
        try:
            user = User.objects.get(username__iexact=username)
            return JsonResponse({
                'is_admin': user.is_staff or user.is_superuser,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'username': user.username,
                'full_name': user.get_full_name() or user.username
            })
        except User.DoesNotExist:
            return JsonResponse({
                'is_admin': False,
                'error': 'User not found'
            }, status=404)
    else:
        # New behavior: check current user session
        if request.user.is_authenticated:
            return JsonResponse({
                'is_authenticated': True,
                'is_admin': request.user.is_staff or request.user.is_superuser,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'username': request.user.username,
                'full_name': request.user.get_full_name() or request.user.username
            })
        else:
            return JsonResponse({
                'is_authenticated': False,
                'is_admin': False
            })

@login_required(login_url='forum')
def api_user_notifications_count(request):
    """API: Get unread notifications count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

def api_get_categories(request):
    """API: Get all categories for registration form"""
    try:
        categories = Category.objects.all().values('id', 'name', 'description').order_by('name')
        return JsonResponse({
            'success': True,
            'categories': list(categories),
            'total': len(list(categories))
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@admin_login_required
def api_users_list(request):
    """API: Get list of all users (Admin only)"""
    users = User.objects.filter(is_active=True).values('id', 'username', 'email').order_by('username')
    return JsonResponse({
        'users': list(users),
        'total': len(list(users))
    })


@require_POST
def api_ai_chat(request):
    """API: Proxy AI chat requests to OpenRouter with server-side cache."""
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Payload JSON không hợp lệ.'}, status=400)

    user_message = (payload.get('message') or '').strip()
    history = payload.get('history') or []

    if not user_message:
        return JsonResponse({'success': False, 'error': 'Thiếu nội dung câu hỏi.'}, status=400)

    api_key = getattr(settings, 'OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return JsonResponse(
            {
                'success': False,
                'error': 'Chưa cấu hình OPENROUTER_API_KEY trên server.',
            },
            status=500,
        )

    model_name = getattr(settings, 'OPENROUTER_MODEL', 'google/gemma-4-26b-a4b-it:free')

    messages = []
    if isinstance(history, list):
        for item in history[-10:]:
            role = (item.get('role') or '').strip()
            content = (item.get('content') or '').strip()
            if role in {'user', 'assistant'} and content:
                msg = {'role': role, 'content': content}
                if role == 'assistant' and item.get('reasoning_details') is not None:
                    msg['reasoning_details'] = item.get('reasoning_details')
                messages.append(msg)
    messages.append({'role': 'user', 'content': user_message})

    cache_payload = {
        'model': model_name,
        'messages': messages,
    }
    cache_digest = hashlib.sha256(
        json.dumps(cache_payload, ensure_ascii=False, sort_keys=True).encode('utf-8')
    ).hexdigest()
    cache_key = f'ai_chat_v1:{cache_digest}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({'success': True, 'reply': cached, 'cached': True})

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': getattr(settings, 'OPENROUTER_HTTP_REFERER', 'http://127.0.0.1:8000'),
        'X-Title': getattr(settings, 'OPENROUTER_APP_TITLE', 'MomCare AI Assistant'),
    }

    body = {
        'model': model_name,
        'messages': messages,
        'extra_body': {'reasoning': {'enabled': True}},
    }

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=body,
            timeout=45,
        )
    except requests.RequestException as exc:
        return JsonResponse({'success': False, 'error': f'Lỗi kết nối AI: {exc}'}, status=502)

    if response.status_code >= 400:
        try:
            err_data = response.json()
            error_message = err_data.get('error', {}).get('message') or str(err_data)
        except Exception:
            error_message = response.text
        return JsonResponse({'success': False, 'error': f'OpenRouter lỗi: {error_message}'}, status=502)

    try:
        data = response.json()
        response_message = data['choices'][0]['message']
        reply = response_message['content']
        reasoning_details = response_message.get('reasoning_details')
    except Exception:
        return JsonResponse({'success': False, 'error': 'Phản hồi AI không hợp lệ.'}, status=502)

    if not isinstance(reply, str) or not reply.strip():
        return JsonResponse({'success': False, 'error': 'AI không trả về nội dung.'}, status=502)

    cache.set(cache_key, reply, timeout=600)
    return JsonResponse(
        {
            'success': True,
            'reply': reply,
            'reasoning_details': reasoning_details,
            'cached': False,
        }
    )

@require_POST
def like_post(request, post_id):
    """API: Like/Unlike post - returns JSON instead of redirect"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Vui lòng đăng nhập để thích bài viết',
            'authenticated': False
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'total_likes': post.total_likes()
    })

@require_POST
def like_comment(request, comment_id):
    """API: Like/Unlike comment - returns JSON instead of redirect"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Vui lòng đăng nhập để thích bình luận',
            'authenticated': False
        }, status=401)
    
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'total_likes': comment.likes.count()
    })


@require_http_methods(["GET"])
def get_post_comments(request, post_id):
    """API: Fetch all comments for a post - returns JSON"""
    try:
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post, is_hidden=False).select_related('author', 'parent').prefetch_related('likes').order_by('created_at')
        role_context = _get_user_role_context(request)
        can_view_anonymous_identity = role_context.get('can_verify_posts', False)

        comments_data = [
            _serialize_comment(c, request.user, can_view_anonymous_identity)
            for c in comments
        ]
        
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'total_comments': len(comments_data)
        })
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Bài viết không tồn tại'
        }, status=404)


# ========== ADMIN CATEGORY API ==========

@admin_login_required
@require_http_methods(['POST', 'PUT', 'DELETE'])
def admin_manage_category(request, category_id=None):
    """Manage categories: Create, Edit, Delete"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        if request.method == 'POST':
            # Create new category
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return JsonResponse({'error': 'Tên danh mục không được để trống'}, status=400)
            
            if Category.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': 'Danh mục này đã tồn tại'}, status=400)
            
            category = Category.objects.create(name=name, description=description)
            
            # Log activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action_type='category_create',
                action_description=f'Created category: {name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Danh mục đã được tạo',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                }
            })
        
        elif request.method == 'PUT' and category_id:
            # Edit category
            category = get_object_or_404(Category, id=category_id)
            name = data.get('name', '').strip() or category.name
            description = data.get('description', '').strip() or category.description
            
            # Check name uniqueness
            if name != category.name and Category.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': 'Tên danh mục này đã tồn tại'}, status=400)
            
            category.name = name
            category.description = description
            category.save()
            
            # Log activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action_type='category_edit',
                action_description=f'Edited category: {name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Danh mục đã được cập nhật',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                }
            })
        
        elif request.method == 'DELETE' and category_id:
            # Delete category
            category = get_object_or_404(Category, id=category_id)
            
            # Check if category has posts
            post_count = category.posts.count()
            if post_count > 0:
                return JsonResponse({
                    'error': 'Không thể xóa danh mục đang có bài viết',
                    'post_count': post_count
                }, status=400)
            
            category_name = category.name
            try:
                category.delete()
            except ProtectedError:
                return JsonResponse({
                    'error': 'Không thể xóa danh mục đang có bài viết',
                    'post_count': category.posts.count()
                }, status=400)
            
            # Log activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action_type='category_delete',
                action_description=f'Deleted category: {category_name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Danh mục đã được xóa'
            })
        
        return JsonResponse({'error': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== ADMIN ACCOUNT API ==========

@admin_login_required
@require_http_methods(['POST'])
def admin_create_user(request):
    """Create new user account"""
    try:
        data = json.loads(request.body) if request.body else {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        full_name = data.get('full_name', '').strip()
        user_type = data.get('user_type', 'user')  # user, doctor, admin
        password = data.get('password', '').strip()
        
        # Validation
        if not username or not email or not password:
            return JsonResponse({'error': 'Username, email và mật khẩu không được để trống'}, status=400)
        
        if User.objects.filter(username__iexact=username).exists():
            return JsonResponse({'error': 'Username đã tồn tại'}, status=400)
        
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({'error': 'Email đã tồn tại'}, status=400)
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = full_name
        
        if user_type == 'admin':
            user.is_staff = True
        
        user.save()
        
        # Create or update profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if user_type in ['user', 'doctor', 'admin']:
            profile.user_type = user_type if user_type != 'admin' else 'user'
            profile.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_create',
            action_description=f'Created user: {username} ({user_type})',
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tài khoản {username} đã được tạo',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.first_name
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_login_required
@require_http_methods(['PUT', 'PATCH'])
def admin_update_user(request, user_id):
    """Update user information"""
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body) if request.body else {}
        
        if user.is_staff and request.user.id != user.id:
            return JsonResponse({'error': 'Không thể chỉnh sửa tài khoản quản trị viên'}, status=403)
        
        # Update basic info
        if 'email' in data:
            new_email = data['email'].strip()
            if new_email and User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
                return JsonResponse({'error': 'Email đã tồn tại'}, status=400)
            user.email = new_email
        
        if 'full_name' in data:
            user.first_name = data['full_name'].strip()
        
        user.save()
        
        # Update profile
        profile = user.profile
        if 'user_type' in data and data['user_type'] in ['user', 'doctor']:
            profile.user_type = data['user_type']
            if data['user_type'] == 'doctor':
                profile.is_verified_doctor = True
            else:
                profile.is_verified_doctor = False
        
        profile.save()
        
        if not user.is_active:
            user.is_active = True
            user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_edit',
            action_description=f'Edited user: {user.username}',
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tài khoản {user.username} đã được cập nhật'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_login_required
@require_POST
def admin_lock_user(request, user_id):
    """Lock user account (prevent login)"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        if user.is_staff:
            return JsonResponse({'error': 'Không thể khóa tài khoản quản trị viên'}, status=403)
        
        user.is_active = False
        user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_lock',
            action_description=f'Locked user: {user.username}',
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tài khoản {user.username} đã bị khóa'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_login_required
@require_POST
def admin_unlock_user(request, user_id):
    """Unlock user account (allow login)"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        user.is_active = True
        user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action_type='user_unlock',
            action_description=f'Unlocked user: {user.username}',
            target_user=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Tài khoản {user.username} đã được mở khóa'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== IMAGE UPLOAD API ==========

@login_required
@require_POST
def upload_image(request):
    """
    API endpoint for uploading images to Cloudinary only
    Accepts multipart/form-data with 'image' file field
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Không tìm thấy tệp hình ảnh'
            }, status=400)
        
        image_file = request.FILES['image']
        folder = request.POST.get('folder', 'momcare/posts')
        
        # Validate file
        if not image_file.name:
            return JsonResponse({
                'success': False,
                'error': 'Tên tệp không hợp lệ'
            }, status=400)
        
        # Check file size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'Tệp quá lớn. Kích thước tối đa: 10MB'
            }, status=400)
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': f'Định dạng không hỗ trợ. Vui lòng chọn: JPG, PNG, WebP hoặc GIF'
            }, status=400)
        
        # Try uploading to Cloudinary
        logger.info(f"Attempting Cloudinary upload for: {image_file.name}")
        result = CloudinaryService.upload_image(
            image_file,
            folder=folder,
            tags=[f'user_{request.user.id}'],
        )
        
        if result:
            logger.info(f"✓ Cloudinary upload successful: {result['secure_url']}")
            return JsonResponse({
                'success': True,
                'secure_url': result['secure_url'],
                'public_id': result['public_id'],
                'width': result.get('width', 0),
                'height': result.get('height', 0),
                'format': result.get('format', 'unknown'),
                'message': 'Tải lên thành công',
                'source': 'cloudinary'
            })
        logger.error(f"Cloudinary upload failed for: {image_file.name}")
        return JsonResponse({
            'success': False,
            'error': 'Không thể tải ảnh lên Cloudinary. Vui lòng thử lại sau.'
        }, status=503)
            
    except Exception as e:
        logger.error(f'Upload endpoint error: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Lỗi máy chủ. Vui lòng thử lại sau.'
        }, status=500)

