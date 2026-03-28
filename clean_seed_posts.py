#!/usr/bin/env python
"""
Clean and seed script to create exactly 3 test posts with different authors
Run with: python be/clean_seed_posts.py from the MC directory
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dien_dan_web_django.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from forum.models import Category, Post

def clean_and_seed():
    # Delete all existing posts
    print("🗑️  Deleting old posts...")
    Post.objects.all().delete()
    print(f"✓ Deleted all posts")
    
    # Create categories
    category_post_natal, _ = Category.objects.get_or_create(
        slug='sau-sinh',
        defaults={'name': 'Sau sinh & chăm sóc mẹ', 'color_dot': 'pink'}
    )
    
    category_nutrition, _ = Category.objects.get_or_create(
        slug='dinh-duong',
        defaults={'name': 'Dinh dưỡng & sinh hoạt', 'color_dot': 'green'}
    )
    
    # Create or get users with different names
    users = [
        {
            'username': 'buily',
            'first_name': 'Bùi',
            'last_name': 'Ly',
        },
        {
            'username': 'minhanh',
            'first_name': 'Minh',
            'last_name': 'Anh',
        },
        {
            'username': 'holy',
            'first_name': 'Hồ',
            'last_name': 'Ly',
        },
    ]
    
    user_objects = []
    for user_data in users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name']
            }
        )
        user_objects.append(user)
        status = "Created" if created else "Already exists"
        print(f"  ✓ User: {user.get_full_name()} ({status})")
    
    # Create exactly 3 posts
    posts_data = [
        {
            'title': 'Sau sinh 3 tháng có kinh từ tuần đầu sau',
            'content': 'Sau sinh 3 tháng có kinh từ tuần đầu sau sinh. Thăng thứ 2 vấn đề dùng ngày, nhưng sang tháng thứ 3 lại lệch chu kỳ và sau kỳ kinh có ra dịch màu sắm. Em hỏi lo lắng, không biết tính trạng này có bình thường sau sinh không a?',
            'author': user_objects[0],
            'category': category_post_natal,
            'verified_by_expert': False,
        },
        {
            'title': 'Kinh nghiệm 3 tháng đầu thai kỳ - Những điều mẹ bầu cần biết',
            'content': 'Chia sẻ kinh nghiệm trong 3 tháng đầu mang thai, từ việc ăn uống đến chăm sóc sức khỏe. Đây là giai đoạn rất quan trọng để đảm bảo thai nhi phát triển khỏe mạnh.',
            'author': user_objects[1],
            'category': category_nutrition,
            'verified_by_expert': True,
        },
        {
            'title': 'Lần đầu làm mẹ: Cách tắm cho trẻ sơ sinh không bị sặc nước',
            'content': 'Tắm cho bé yêu là một trải nghiệm tuyệt vời nhưng cũng đầy lo lắng với những mẹ lần đầu. Hãy chuẩn bị nước ấm khoảng 37 độ C và luôn giữ an toàn cho bé.',
            'author': user_objects[2],
            'category': category_post_natal,
            'verified_by_expert': False,
        },
    ]
    
    print("\n🌱 Creating posts...")
    for i, post_data in enumerate(posts_data):
        post = Post.objects.create(
            title=post_data['title'],
            content=post_data['content'],
            author=post_data['author'],
            category=post_data['category'],
            verified_by_expert=post_data['verified_by_expert'],
        )
        verified_status = "✓ (kiểm định)" if post_data['verified_by_expert'] else "✗ (chưa kiểm định)"
        print(f"  {i+1}. {post.title[:50]}... by {post.author.get_full_name()} {verified_status}")

if __name__ == '__main__':
    print("🧹 Cleaning and seeding posts...\n")
    clean_and_seed()
    print("\n✅ Done! Now you have exactly 3 posts with different authors.")
