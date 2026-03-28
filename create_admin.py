#!/usr/bin/env python
"""
Script to create admin account
Run with: python create_admin.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dien_dan_web_django.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User

# Create or update admin account
if User.objects.filter(username='admin').exists():
    admin = User.objects.get(username='admin')
    admin.set_password('123456')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    print("✅ Admin account updated")
else:
    admin = User.objects.create_superuser('admin', 'admin@momcare.com', '123456')
    print("✅ Admin account created")

print("\n📝 Credentials:")
print("   Username: admin")
print("   Password: 123456")
print("\n🔗 Access at: http://localhost:8000/admin-panel/")
