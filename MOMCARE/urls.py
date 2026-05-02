"""
URL configuration for moncare_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from momcare_forum import views as forum_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main pages
    path('', forum_views.landing_page, name='landing'),
    path('forum/', forum_views.forum_home, name='forum'),
    path('profile/', forum_views.user_profile, name='profile'),
    path('profile/info/', forum_views.personal_info, name='profile_info'),
    path('profile/<str:username>/', forum_views.user_profile, name='profile_view'),
    
    # Authentication (modal-based)
    path('logout/', forum_views.user_logout, name='logout'),
    path('forgot-password/step1/', forum_views.forgot_password_step1, name='forgot_password_step1'),
    path('forgot-password/step2/', forum_views.forgot_password_step2, name='forgot_password_step2'),
    path('forgot-password/step3/', forum_views.forgot_password_step3, name='forgot_password_step3'),
    
    # Post management
    path('post/create/', forum_views.create_post, name='create_post'),  # POST only (requires @require_POST decorator)
    path('post/<int:post_id>/', forum_views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', forum_views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', forum_views.delete_post, name='delete_post'),
    path('post/<int:post_id>/comment/', forum_views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/', forum_views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', forum_views.delete_comment, name='delete_comment'),
    
    # Reporting
    path('report/create/', forum_views.create_report, name='create_report'),
    
    # Notifications
    path('notifications/', forum_views.notifications, name='notifications'),
    path('notification/<int:notification_id>/', forum_views.notification_detail, name='notification_detail'),
    path('notifications/mark-all-read/', forum_views.mark_all_as_read, name='mark_all_as_read'),
    path('api/notification/<int:notification_id>/edit/', forum_views.edit_notification, name='edit_notification'),
    path('api/notification/<int:notification_id>/delete/', forum_views.delete_notification, name='delete_notification'),
    path('api/notifications/delete-multiple/', forum_views.delete_multiple_notifications, name='delete_multiple_notifications'),
    path('api/notifications/create-system/', forum_views.create_system_notification, name='create_system_notification'),
    
    # Expert verification
    path('post/<int:post_id>/verify/', forum_views.verify_post, name='verify_post'),
    path('post/<int:post_id>/unverify/', forum_views.unverify_post, name='unverify_post'),
    
    path('admin-login/', forum_views.admin_login, name='admin_login'),
    path('admin-logout/', forum_views.user_logout, name='admin_logout'),
    path('admin-panel/', forum_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/categories/', forum_views.admin_categories, name='admin_categories'),
    path('admin-panel/reports/', forum_views.admin_reports, name='admin_reports'),
    path('admin-panel/accounts/', forum_views.admin_accounts, name='admin_accounts'),
    path('admin-panel/posts/', forum_views.admin_posts, name='admin_posts'),
    path('admin-panel/notifications/', forum_views.admin_notifications, name='admin_notifications'),
    path('admin-panel/dashboard-advanced/', forum_views.admin_advanced_dashboard, name='admin_advanced_dashboard'),
    path('admin-panel/users-advanced/', forum_views.admin_user_management, name='admin_user_management'),
    path('admin-panel/moderation/', forum_views.admin_moderation, name='admin_moderation'),
    path('admin-panel/settings/', forum_views.admin_settings, name='admin_settings'),
    path('admin-panel/activity-logs/', forum_views.admin_activity_logs, name='admin_activity_logs'),
    path('admin-panel/report/<int:report_id>/process/', forum_views.process_report, name='process_report'),
    
    # Admin Actions
    path('api/admin/user/<int:user_id>/role/', forum_views.admin_change_user_role, name='admin_change_user_role'),
    path('api/admin/user/<int:user_id>/delete/', forum_views.admin_delete_user, name='admin_delete_user'),
    path('api/admin/posts/bulk-action/', forum_views.admin_bulk_post_action, name='admin_bulk_post_action'),
    
    # API endpoints
    path('api/login-validate/', forum_views.api_login_validate, name='api_login_validate'),
    path('api/register/send-otp/', forum_views.api_register_send_otp, name='api_register_send_otp'),
    path('api/register/verify-otp/', forum_views.api_register_verify_otp, name='api_register_verify_otp'),
    path('api/register/resend-otp/', forum_views.api_register_resend_otp, name='api_register_resend_otp'),
    path('api/register/complete/', forum_views.api_register_complete, name='api_register_complete'),
    path('api/logout/', forum_views.user_logout, name='api_logout'),
    path('api/check-admin-status/', forum_views.check_admin_status, name='check_admin_status'),
    path('api/categories/', forum_views.api_get_categories, name='api_get_categories'),
    path('api/notifications-count/', forum_views.api_user_notifications_count, name='api_notifications_count'),
    path('api/users-list/', forum_views.api_users_list, name='api_users_list'),
    path('api/profile/update/', forum_views.api_update_personal_info, name='api_update_personal_info'),
    path('api/profile/change-password/', forum_views.api_change_password, name='api_change_password'),
    path('api/post/<int:post_id>/like/', forum_views.like_post, name='like_post'),
    path('api/post/<int:post_id>/comments/', forum_views.get_post_comments, name='get_post_comments'),
    path('api/comment/<int:comment_id>/like/', forum_views.like_comment, name='like_comment'),
    path('api/upload-image/', forum_views.upload_image, name='upload_image'),
    path('api/post/<int:post_id>/verification-history/', forum_views.post_verification_history, name='post_verification_history'),
    path('api/ai-chat/', forum_views.api_ai_chat, name='api_ai_chat'),
    
    # Admin Category API
    path('api/admin/category/', forum_views.admin_manage_category, name='admin_manage_category'),
    path('api/admin/category/<int:category_id>/', forum_views.admin_manage_category, name='admin_manage_category_detail'),
    
    # Admin Account API
    path('api/admin/user/create/', forum_views.admin_create_user, name='admin_create_user'),
    path('api/admin/user/<int:user_id>/edit/', forum_views.admin_update_user, name='admin_update_user'),
    path('api/admin/user/<int:user_id>/lock/', forum_views.admin_lock_user, name='admin_lock_user'),
    path('api/admin/user/<int:user_id>/unlock/', forum_views.admin_unlock_user, name='admin_unlock_user'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += [
    path('<path:invalid_path>', forum_views.custom_404, name='custom_404'),
]
