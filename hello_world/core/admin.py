from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Badge, UserBadge,
    Activity, ActivityProof, ActivityVerification,
    Rating, Board, Category, Post, PostImage, Comment, PostLike,
    Event, Notification, ManagementDocument,
    Group, GroupMember, GroupPost, GroupComment, GroupChat,
    MemberGrade, BoardGradePermission,
    Survey, SurveyQuestion, SurveyResponse,
    PublicChat, DirectMessage, ChatHistory, ChatPoll,
)

# ============================================================
# 회원
# ============================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'nickname', 'dong', 'ho', 'mileage_points', 'manners_score', 'is_verified', 'date_joined')
    list_filter   = ('is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'nickname', 'dong', 'ho')
    ordering      = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('입주민 정보', {'fields': ('nickname', 'dong', 'ho', 'unit_number', 'bio', 'avatar')}),
        ('활동 정보',   {'fields': ('mileage_points', 'manners_score', 'is_verified', 'current_badges')}),
    )

# ============================================================
# 배지
# ============================================================
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'required_points', 'required_activities', 'is_active')
    list_filter   = ('category', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('required_points', 'required_activities', 'is_active')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'badge', 'earned_at')
    list_filter   = ('badge',)
    search_fields = ('user__nickname', 'user__username', 'badge__title')
    raw_id_fields = ('user', 'badge')

# ============================================================
# 활동 / 인증
# ============================================================
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display  = ('name', 'activity_type', 'base_points', 'points_per_hour', 'is_active')
    list_filter   = ('activity_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('base_points', 'points_per_hour', 'is_active')

@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display  = ('user', 'activity', 'status', 'points_earned', 'submitted_at')
    list_filter   = ('status', 'activity')
    search_fields = ('user__nickname', 'user__username')
    list_editable = ('status',)
    actions       = ['approve_selected', 'reject_selected']
    raw_id_fields = ('user', 'activity')

    def approve_selected(self, request, queryset):
        for proof in queryset.filter(status='pending'):
            proof.status = 'approved'
            proof.save()
        self.message_user(request, f"{queryset.count()}개 승인 완료")
    approve_selected.short_description = "✅ 선택 항목 승인"

    def reject_selected(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"{queryset.count()}개 반려 완료")
    reject_selected.short_description = "❌ 선택 항목 반려"

# ============================================================
# 게시판
# ============================================================
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display  = ('name', 'board_type', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'board', 'created_at', 'view_count', 'is_active')
    list_filter   = ('board', 'is_active')
    search_fields = ('title', 'content', 'author__nickname')
    raw_id_fields = ('author', 'board')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ('author', 'post', 'content', 'created_at', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('content', 'author__nickname')
    raw_id_fields = ('author', 'post')

# ============================================================
# 관리 문서
# ============================================================
@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'author', 'view_count', 'is_active', 'created_at')
    list_filter   = ('category', 'is_active')
    search_fields = ('title', 'content')
    list_editable = ('is_active',)
    raw_id_fields = ('author',)

# ============================================================
# 이웃 온기 점수
# ============================================================
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display  = ('rater', 'rated_user', 'score', 'created_at')
    list_filter   = ('score',)
    search_fields = ('rater__nickname', 'rated_user__nickname')
    raw_id_fields = ('rater', 'rated_user')

# ============================================================
# 소모임
# ============================================================
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'group_type', 'leader', 'is_active', 'created_at')
    list_filter   = ('group_type', 'is_active')
    search_fields = ('name', 'description', 'leader__nickname')
    raw_id_fields = ('leader',)

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display  = ('user', 'group', 'role', 'joined_at')
    list_filter   = ('role',)
    raw_id_fields = ('user', 'group')

# ============================================================
# 봉사 일정
# ============================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ('title', 'activity_type', 'start_time', 'end_time', 'max_participants', 'is_active')
    list_filter   = ('activity_type', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)

# ============================================================
# 알림
# ============================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter   = ('notification_type', 'is_read')
    search_fields = ('recipient__nickname', 'title', 'message')
    raw_id_fields = ('recipient',)

# ============================================================
# 설문
# ============================================================
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display  = ('title', 'creator', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('title', 'creator__nickname')
    raw_id_fields = ('creator',)

# ============================================================
# 회원 등급
# ============================================================
@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'level', 'required_points', 'color_code')
    list_editable = ('required_points', 'color_code')
    ordering      = ('level',)

