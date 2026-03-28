from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

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
        verbose_name_plural = "Categories"

class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="posts", verbose_name="Danh mục")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", verbose_name="Người đăng")
    
    verified_by_expert = models.BooleanField(default=False, verbose_name="Được chuyên gia kiểm duyệt")
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Bài viết")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", verbose_name="Người bình luận")
    content = models.TextField(verbose_name="Nội dung")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    class Meta:
        ordering = ['created_at']
