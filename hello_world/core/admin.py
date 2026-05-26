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

    @admin.action(description='선택한 활동 인증 승인')
    def approve_proofs(self, request, queryset):
        for proof in queryset:
            # 이미 승인된 건은 중복 포인트 적립 방지
            if proof.status == 'approved':
                continue
            
            proof.status = 'approved'
            proof.approved_by = request.user
            proof.approved_at = timezone.now()
            
            # 포인트 자동 계산
            if proof.points_earned == 0:
                proof.points_earned = int(
                    proof.activity.base_points +
                    (proof.activity.points_per_hour * proof.duration_hours)
                )
            proof.save()
            
            # 사용자 마일리지 적립
            proof.user.mileage_points += proof.points_earned
            proof.user.save()
            
        self.message_user(request, f'{queryset.count()}건 승인 완료 및 포인트 적립됨')

    @admin.action(description='선택한 활동 인증 반려')
    def reject_proofs(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()}건 반려됨')