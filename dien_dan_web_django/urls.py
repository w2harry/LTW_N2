"""
URL configuration for dien_dan_web_django project.

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
from django.views.generic import TemplateView
from django.contrib.auth.views import logout_then_login
from forum import views as forum_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', forum_views.landing_page, name='landing'),
    path('forum/', forum_views.forum_home, name='forum'),
    path('profile/', forum_views.user_profile, name='profile'),
    path('profile/info/', TemplateView.as_view(template_name='auth/personal_info.html'), name='profile_info'),
    path('admin-login/', forum_views.admin_login, name='admin_login'),
    path('admin-logout/', logout_then_login, {'login_url': '/admin-login/'}, name='admin_logout'),
    path('admin-panel/', forum_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/categories/', forum_views.admin_categories, name='admin_categories'),
    path('admin-panel/reports/', forum_views.admin_reports, name='admin_reports'),
    path('admin-panel/accounts/', forum_views.admin_accounts, name='admin_accounts'),
    # API endpoints
    path('api/check-admin-status/', forum_views.check_admin_status, name='check_admin_status'),
]
