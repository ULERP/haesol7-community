from django.contrib import admin
from django.utils import timezone
from .models import Activity, ActivityProof, Post, Group, Meetup

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'activity_type', 'base_points', 'is_active')
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at')

@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'scheduled_at')

@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'title', 'duration_hours', 'status', 'points_earned', 'submitted_at']
    list_filter = ['status', 'activity']
    list_editable = ['status', 'points_earned']
    search_fields = ['user__username', 'title']
    readonly_fields = ['submitted_at', 'approved_at', 'approved_by']
    actions = ['approve_proofs', 'reject_proofs']

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'approved' and obj.points_earned == 0:
                obj.points_earned = int(
                    obj.activity.base_points +
                    obj.activity.points_per_hour * obj.duration_hours
                )
            if obj.status == 'approved':
                from django.utils import timezone
                obj.approved_at = timezone.now()
                obj.approved_by = request.user
        super().save_model(request, obj, form, change)

    def approve_proofs(self, request, queryset):
        from django.utils import timezone
        count = 0
        for proof in queryset.filter(status='pending'):
            proof.status = 'approved'
            proof.approved_at = timezone.now()
            proof.approved_by = request.user
            if proof.points_earned == 0:
                proof.points_earned = int(
                    proof.activity.base_points +
                    proof.activity.points_per_hour * proof.duration_hours
                )
            proof.save()
            count += 1
        self.message_user(request, f'{count}건 승인! 마일리지 자동 적립 완료.')
    approve_proofs.short_description = '선택 활동 승인 + 마일리지 자동 적립'

    def reject_proofs(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{count}건 반려됐습니다.')
    reject_proofs.short_description = '선택 활동 반려'

from .models import Survey, SurveyQuestion, SurveyResponse

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'status', 'total_responses', 'is_anonymous', 'ends_at', 'created_at']
    list_filter = ['status', 'is_anonymous', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def total_responses(self, obj):
        return obj.responses.count()
    total_responses.short_description = '응답 수'

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ['survey', 'text', 'question_type', 'is_required', 'order']
    list_filter = ['question_type', 'is_required']
    search_fields = ['text', 'survey__title']
    ordering = ['survey', 'order']

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'respondent', 'submitted_at']
    list_filter = ['survey', 'submitted_at']
    search_fields = ['survey__title', 'respondent__username']
    readonly_fields = ['survey', 'respondent', 'answers', 'submitted_at']
    date_hierarchy = 'submitted_at'
    ordering = ['-submitted_at']
