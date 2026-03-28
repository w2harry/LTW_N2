from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Post, Comment
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST

def forum_home(request):
    """
    View cho trang chủ Diễn đàn: Hiển thị danh sách Categories và Posts.
    Hỗ trợ tìm kiếm và lọc theo danh mục.
    """
    categories = Category.objects.all()
    posts = Post.objects.all().order_by('-created_at')
    
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
    
    context = {
        'categories': categories,
        'posts': posts,
        'selected_category': category_id,
        'search_query': query,
    }
    return render(request, 'auth/forum.html', context)

def user_profile(request):
    """
    View cho trang cá nhân người dùng.
    Hiện tại lấy dữ liệu mẫu cho user 'minhanh' (username viết thường).
    """
    # Lấy user có username 'minhanh' hoặc user đầu tiên nếu ko tìm thấy
    target_user = User.objects.filter(username__iexact='minhanh').first() or User.objects.first()
    posts = Post.objects.filter(author=target_user).order_by('-created_at')
    
    context = {
        'posts': posts,
        'post_count': posts.count(),
        'target_user': target_user,
    }
    return render(request, 'auth/profile.html', context)

def landing_page(request):
    """
    View cho trang Landing: Hiển thị một vài bài viết nổi bật (nhiều likes nhất).
    """
    featured_posts = Post.objects.annotate(num_likes=Count('likes')).order_by('-num_likes')[:3]
    context = {
        'featured_posts': featured_posts,
    }
    return render(request, 'auth/landing.html', context)


# ========== ADMIN VIEWS ==========

def admin_login_required(view_func):
    """Decorator: Yêu cầu login + is_staff để vào admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin-login/')
        if not request.user.is_staff:
            return HttpResponseForbidden("❌ Bạn không có quyền vào admin panel")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_login(request):
    """Admin Login Page"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin-panel/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect('/admin-panel/')
            else:
                error = "❌ Tài khoản không có quyền admin"
        else:
            error = "❌ Username hoặc password không đúng"
        
        return render(request, 'auth/admin_login.html', {'error': error, 'username': username})
    
    return render(request, 'auth/admin_login.html', {})


@admin_login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    stats = {
        'total_posts': Post.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_categories': Category.objects.count(),
    }
    return render(request, 'auth/admin_dashboard.html', stats)


@admin_login_required
def admin_posts(request):
    """Admin Posts Management"""
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'auth/admin_posts.html', {'posts': posts})


@admin_login_required
def admin_categories(request):
    """Admin Categories Management"""
    categories = Category.objects.all()
    return render(request, 'auth/admin_categories.html', {'categories': categories})


@admin_login_required
def admin_accounts(request):
    """Admin Accounts Management"""
    users = User.objects.all()
    return render(request, 'auth/admin_accounts.html', {'users': users})


@admin_login_required
def admin_reports(request):
    """Admin Reports Management"""
    return render(request, 'auth/admin_reports.html', {})


# ========== API ENDPOINTS ==========

def check_admin_status(request):
    """API: Check if username is admin"""
    username = request.GET.get('username', '')
    
    try:
        user = User.objects.get(username__iexact=username)
        return JsonResponse({
            'is_admin': user.is_staff,
            'username': user.username,
            'full_name': user.get_full_name() or user.username
        })
    except User.DoesNotExist:
        return JsonResponse({
            'is_admin': False,
            'username': username,
            'full_name': username
        })
