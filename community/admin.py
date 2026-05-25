from django.contrib import admin
from .models import Board, Post, Comment
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['is_active', 'order']
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'board', 'tag', 'view_count', 'created_at']
