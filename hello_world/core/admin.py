from django.contrib import admin
from .models import Activity, ActivityProof, Post, Group, Meetup

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    # 'created_at'을 제거하고 모델에 존재하는 필드만 사용합니다.
    list_display = ('name', 'activity_type', 'base_points', 'is_active')
    search_fields = ('name',)

@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'status', 'submitted_at')
    list_filter = ('status',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at')

@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'scheduled_at')