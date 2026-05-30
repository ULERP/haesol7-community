
from django.contrib import admin
from .models import (
    CustomUser, ComplaintCategory, NoticeCategory,
    Complaint, Notice, Letter
)

@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'icon', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering      = ['order']

@admin.register(NoticeCategory)
class NoticeCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'icon', 'color', 'order', 'is_active']
    list_editable = ['order', 'is_active', 'color']
    ordering      = ['order']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display  = ['title', 'author', 'category', 'status', 'is_anonymous', 'created_at']
    list_filter   = ['status', 'category']
    search_fields = ['title', 'author__nickname']
    readonly_fields = ['author', 'created_at']

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display  = ['title', 'notice_type', 'is_pinned', 'author', 'created_at']
    list_editable = ['is_pinned']
    list_filter   = ['notice_type']

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display  = ['username', 'nickname', 'dong', 'ho', 'is_verified', 'is_staff']
    list_editable = ['is_verified']
    list_filter   = ['is_verified', 'is_staff']
    search_fields = ['username', 'nickname', 'dong']

from .models import MemberGrade, Board, BoardGradePermission

@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'required_points', 'required_activities', 'order', 'is_active']
    list_editable = ['required_points', 'order', 'is_active']
    ordering      = ['order']

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display  = ['name', 'board_type', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering      = ['order']
