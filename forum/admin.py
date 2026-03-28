from django.contrib import admin
from .models import Category, Post, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color_dot', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('color_dot',)
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'verified_by_expert', 'created_at')
    list_filter = ('category', 'verified_by_expert', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_select_related = ('author', 'category')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    list_select_related = ('author', 'post')
