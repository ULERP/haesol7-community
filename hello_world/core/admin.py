"""
해솔7 지킴이 커뮤니티 - 관리자 페이지
모든 모델의 Admin 클래스 정의
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.core.mail import send_mail
import random, string

from .models import (
    AdminActionLog, CustomUser, Badge, UserBadge, UserFollow,
    Activity, ActivityProof, Rating, Board, Post, Comment,
    ManagementDocument, Event, Notification, Group, GroupMember,
    GroupLeaderLog, GroupDissolveVote, MemberGrade,
    Survey, CalendarEvent, SiteConfig, Meetup, MeetupRating,
)


# ════════════════════════════════════════════════════════════════
# 유틸리티
# ════════════════════════════════════════════════════════════════
def _get_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR', '')

def _log(admin_user, target, action, detail, ip):
    AdminActionLog.objects.create(
        admin=admin_user, target_user=target,
        action=action, detail=detail, ip_address=ip
    )


# ════════════════════════════════════════════════════════════════
# 👥 회원 관리
# ════════════════════════════════════════════════════════════════
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display    = ('username', 'nickname', 'dong_ho', 'email',
                       'is_verified_icon', 'is_active', 'is_staff',
                       'mileage_points', 'date_joined')
    list_filter     = ('is_verified', 'is_staff', 'is_active', 'dong')
    search_fields   = ('username', 'nickname', 'dong', 'ho', 'email', 'phone_number')
    ordering        = ('-date_joined',)
    list_per_page   = 30
    list_display_links = ('username', 'nickname')
    actions         = ['action_verify', 'action_unverify',
                       'action_activate', 'action_deactivate',
                       'action_send_temp_password']

    fieldsets = (
        ('🔐 계정 정보', {'fields': ('username', 'password')}),
        ('🏠 입주민 정보', {'fields': (
            'nickname', 'dong', 'ho', 'unit_number', 'phone_number',
            'is_verified', 'profile_image',
        )}),
        ('📧 연락처', {'fields': ('email', 'first_name', 'last_name')}),
        ('🏅 활동 정보', {'fields': (
            'mileage_points', 'manners_score', 'current_badges',
        )}),
        ('🔑 보안', {'fields': (
            'security_question', 'security_answer',
        ), 'classes': ('collapse',)}),
        ('🛡️ 권한', {'fields': (
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions',
        ), 'classes': ('collapse',)}),
        ('📅 기록', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'manners_score')

    def dong_ho(self, obj):
        if obj.dong and obj.ho:
            return f"{obj.dong}동 {obj.ho}호"
        return format_html('<span style="color:#9ca3af;">미입력</span>')
    dong_ho.short_description = '동/호수'
    dong_ho.admin_order_field = 'dong'

    def is_verified_icon(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#1a7a4a;font-weight:700;">✅ 인증</span>')
        return format_html('<span style="color:#7A263A;font-weight:700;">⚠️ 미인증</span>')
    is_verified_icon.short_description = '인증'
    is_verified_icon.admin_order_field = 'is_verified'

    @admin.action(description='✅ 입주민 인증 승인')
    def action_verify(self, request, queryset):
        ip = _get_ip(request)
        count = 0
        for user in queryset.filter(is_verified=False):
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            _log(request.user, user, 'verify', '입주민 인증 승인', ip)
            count += 1
        self.message_user(request, f"✅ {count}명 인증 승인 완료")

    @admin.action(description='❌ 입주민 인증 취소')
    def action_unverify(self, request, queryset):
        ip = _get_ip(request)
        count = 0
        for user in queryset.filter(is_verified=True):
            user.is_verified = False
            user.save(update_fields=['is_verified'])
            _log(request.user, user, 'verify', '입주민 인증 취소', ip)
            count += 1
        self.message_user(request, f"❌ {count}명 인증 취소 완료")

    @admin.action(description='🟢 계정 활성화')
    def action_activate(self, request, queryset):
        ip = _get_ip(request)
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=False):
            user.is_active = True
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'activate', '계정 활성화', ip)
            count += 1
        self.message_user(request, f"🟢 {count}명 활성화 완료")

    @admin.action(description='🔴 계정 비활성화')
    def action_deactivate(self, request, queryset):
        ip = _get_ip(request)
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=True):
            user.is_active = False
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'deactivate', '계정 비활성화', ip)
            count += 1
        self.message_user(request, f"🔴 {count}명 비활성화 완료")

    @admin.action(description='🔑 임시 비밀번호 발급 및 이메일 발송')
    def action_send_temp_password(self, request, queryset):
        ip = _get_ip(request)
        ok, fail = [], []
        for user in queryset:
            if user.is_superuser or not user.email:
                fail.append(f"{user.nickname or user.username}(이메일없음)")
                continue
            tmp = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(tmp)
            user.save(update_fields=['password'])
            try:
                send_mail(
                    '[해솔7 지킴이] 임시 비밀번호 발급',
                    f"{user.nickname or user.username}님,\n임시 비밀번호: {tmp}\n로그인 후 즉시 변경해주세요.",
                    None, [user.email],
                )
                ok.append(user.nickname or user.username)
                _log(request.user, user, 'pw_reset', f"이메일:{user.email[:3]}***", ip)
            except Exception:
                fail.append(f"{user.nickname or user.username}(발송실패)")
        if ok:   self.message_user(request, f"✅ 발송: {', '.join(ok)}", messages.SUCCESS)
        if fail: self.message_user(request, f"⚠️ 실패: {', '.join(fail)}", messages.WARNING)


@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'order', 'required_points', 'required_activities', 'badge_color', 'is_active')
    list_editable = ('required_points', 'required_activities', 'order', 'is_active')
    ordering      = ('order',)
    list_per_page = 10


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'required_points', 'required_activities', 'is_active')
    list_filter   = ('category', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    list_per_page = 20


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'badge', 'earned_at', 'is_displayed')
    list_filter   = ('badge', 'is_displayed')
    search_fields = ('user__nickname', 'badge__title')
    raw_id_fields = ('user', 'badge')
    list_per_page = 30
    readonly_fields = ('earned_at',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display    = ('rater', 'rated_user', 'score', 'short_comment', 'created_at')
    list_filter     = ('score',)
    search_fields   = ('rater__nickname', 'rated_user__nickname')
    raw_id_fields   = ('rater', 'rated_user')
    list_per_page   = 30
    readonly_fields = ('created_at',)

    def short_comment(self, obj):
        return (obj.comment[:30] + '…') if obj.comment and len(obj.comment) > 30 else (obj.comment or '-')
    short_comment.short_description = '한마디'


# ════════════════════════════════════════════════════════════════
# 📋 콘텐츠 관리
# ════════════════════════════════════════════════════════════════
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display  = ('name', 'board_type', 'layout_type', 'order', 'write_permission', 'is_active')
    list_editable = ('order', 'layout_type', 'write_permission', 'is_active')
    search_fields = ('name',)
    list_per_page = 20
    ordering      = ('order',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display    = ('title', 'author', 'board', 'view_count', 'like_count',
                       'is_pinned_icon', 'is_active', 'created_at')
    list_filter     = ('board', 'is_active', 'is_pinned', 'created_at')
    search_fields   = ('title', 'content', 'author__nickname', 'author__username')
    raw_id_fields   = ('author', 'board')
    list_editable   = ('is_active',)
    list_per_page   = 30
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'like_count')
    date_hierarchy  = 'created_at'
    actions         = ['pin_posts', 'unpin_posts', 'hide_posts']

    def is_pinned_icon(self, obj):
        return format_html('<span style="color:#D4B26A;">📌</span>') if obj.is_pinned else '-'
    is_pinned_icon.short_description = '고정'
    is_pinned_icon.admin_order_field = 'is_pinned'

    @admin.action(description='📌 상단 고정')
    def pin_posts(self, request, queryset):
        queryset.update(is_pinned=True)
        self.message_user(request, f"📌 {queryset.count()}개 고정 완료")

    @admin.action(description='📌 고정 해제')
    def unpin_posts(self, request, queryset):
        queryset.update(is_pinned=False)
        self.message_user(request, f"✅ {queryset.count()}개 고정 해제")

    @admin.action(description='🚫 숨김 처리')
    def hide_posts(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"🚫 {queryset.count()}개 숨김 처리")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display    = ('author', 'post_link', 'short_content', 'is_active', 'created_at')
    list_filter     = ('is_active', 'created_at')
    search_fields   = ('content', 'author__nickname', 'post__title')
    raw_id_fields   = ('author', 'post')
    list_editable   = ('is_active',)
    list_per_page   = 30
    readonly_fields = ('created_at',)

    def short_content(self, obj):
        return (obj.content[:40] + '…') if len(obj.content) > 40 else obj.content
    short_content.short_description = '내용'

    def post_link(self, obj):
        return format_html('<a href="/posts/{}/" target="_blank">{}</a>',
                           obj.post.pk, obj.post.title[:20])
    post_link.short_description = '게시글'


@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    list_display    = ('title', 'category', 'author', 'view_count', 'has_file', 'is_active', 'created_at')
    list_filter     = ('category', 'is_active')
    search_fields   = ('title', 'content')
    list_editable   = ('is_active',)
    raw_id_fields   = ('author',)
    list_per_page   = 20
    readonly_fields = ('created_at', 'updated_at', 'view_count')

    def has_file(self, obj):
        return format_html('<span style="color:#1a7a4a;">📎 있음</span>') if obj.file else '-'
    has_file.short_description = '첨부파일'


# ════════════════════════════════════════════════════════════════
# 🤝 소모임 관리
# ════════════════════════════════════════════════════════════════
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'group_type', 'join_type', 'status_badge',
                     'member_count_display', 'creator', 'is_active', 'created_at')
    list_filter   = ('group_type', 'join_type', 'status', 'is_active')
    search_fields = ('name', 'description', 'creator__nickname')
    raw_id_fields = ('creator', 'approved_by')
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at', 'activity_score')
    actions       = ['approve_groups', 'reject_groups']

    fieldsets = (
        ('기본 정보', {'fields': ('name', 'description', 'group_type', 'group_image')}),
        ('설정', {'fields': ('join_type', 'member_limit', 'is_limited', 'expires_at', 'is_public', 'is_active')}),
        ('승인', {'fields': ('status', 'approved_by', 'approved_at')}),
        ('활동', {'fields': ('emblem_level', 'activity_score', 'regular_schedule', 'location')}),
        ('기록', {'fields': ('created_at', 'updated_at')}),
    )

    def status_badge(self, obj):
        colors = {'active':'#1a7a4a','pending':'#D4B26A','dissolving':'#f59e0b','dissolved':'#9ca3af'}
        labels = {'active':'운영중','pending':'승인대기','dissolving':'해체투표중','dissolved':'해체됨'}
        color = colors.get(obj.status, '#9ca3af')
        label = labels.get(obj.status, obj.status)
        return format_html('<span style="color:{};font-weight:700;">{}</span>', color, label)
    status_badge.short_description = '상태'
    status_badge.admin_order_field = 'status'

    def member_count_display(self, obj):
        return format_html('<b>{}명</b>', obj.member_count())
    member_count_display.short_description = '회원수'

    @admin.action(description='✅ 소모임 승인')
    def approve_groups(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='active', approved_by=request.user, approved_at=timezone.now()
        )
        self.message_user(request, f"✅ {count}개 소모임 승인 완료")

    @admin.action(description='❌ 소모임 승인 거부')
    def reject_groups(self, request, queryset):
        count = queryset.filter(status='pending').update(status='dissolved')
        self.message_user(request, f"❌ {count}개 거부 처리")

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('<int:group_id>/change-leader/',
                 self.admin_site.admin_view(self.change_leader_view),
                 name='group_change_leader'),
            path('<int:group_id>/change-leader/confirm/',
                 self.admin_site.admin_view(self.change_leader_confirm),
                 name='group_change_leader_confirm'),
        ]
        return custom + urls

    def change_leader_view(self, request, group_id):
        from django.shortcuts import render, get_object_or_404
        from django.db.models import Q
        group   = get_object_or_404(Group, pk=group_id)
        members = GroupMember.objects.filter(group=group, join_status='approved').select_related('user')
        current = members.filter(role='leader').first()
        q       = request.GET.get('q', '')
        users   = CustomUser.objects.filter(is_active=True).order_by('dong', 'unit_number')
        if q:
            users = users.filter(Q(username__icontains=q)|Q(nickname__icontains=q)|Q(dong__icontains=q))
        return render(request, 'admin/group_change_leader.html', {
            'group': group, 'members': members, 'current_leader': current,
            'all_users': users, 'q': q, 'opts': self.model._meta,
        })

    def change_leader_confirm(self, request, group_id):
        from django.shortcuts import redirect, get_object_or_404, render
        group = get_object_or_404(Group, pk=group_id)
        if request.method != 'POST':
            return redirect(f'/admin/core/group/{group_id}/change-leader/')
        new_id    = request.POST.get('new_leader_id')
        confirmed = request.POST.get('confirmed')
        members   = GroupMember.objects.filter(group=group, join_status='approved').select_related('user')
        current   = members.filter(role='leader').first()
        try:
            new_user = CustomUser.objects.get(id=new_id)
        except CustomUser.DoesNotExist:
            messages.error(request, '❌ 회원을 찾을 수 없습니다.')
            return redirect(f'/admin/core/group/{group_id}/change-leader/')
        if not confirmed:
            return render(request, 'admin/group_change_leader.html', {
                'group': group, 'members': members, 'current_leader': current,
                'new_leader': new_user, 'confirm_step': True, 'opts': self.model._meta,
            })
        if current:
            current.role = 'member'; current.save()
        m, _ = GroupMember.objects.get_or_create(
            group=group, user=new_user,
            defaults={'role':'leader','join_status':'approved'}
        )
        m.role = 'leader'; m.join_status = 'approved'; m.save()
        GroupLeaderLog.objects.create(
            group=group, actor=request.user, action='admin_change', target=new_user,
            detail=f'관리자가 소모임장을 {current.user if current else "없음"} → {new_user}로 변경'
        )
        messages.success(request, f'✅ 소모임장이 {new_user}로 변경되었습니다.')
        return redirect(f'/admin/core/group/{group_id}/change/')


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display  = ('user', 'group', 'role_badge', 'join_status', 'joined_at')
    list_filter   = ('role', 'join_status')
    search_fields = ('user__nickname', 'group__name')
    raw_id_fields = ('user', 'group', 'approved_by')
    list_editable = ('join_status',)
    list_per_page = 30
    readonly_fields = ('joined_at', 'approved_at')
    actions       = ['remove_leader_role']

    def role_badge(self, obj):
        colors = {'leader':'#7A263A','moderator':'#D4B26A','member':'#6b7280'}
        labels = {'leader':'👑 리더','moderator':'🛡️ 운영진','member':'회원'}
        return format_html('<span style="color:{};font-weight:600;">{}</span>',
                           colors.get(obj.role,'#6b7280'), labels.get(obj.role, obj.role))
    role_badge.short_description = '역할'
    role_badge.admin_order_field = 'role'

    @admin.action(description='👑 리더 권한 해제 (일반 멤버로)')
    def remove_leader_role(self, request, queryset):
        count = 0
        for m in queryset.filter(role='leader'):
            GroupLeaderLog.objects.create(
                group=m.group, actor=request.user, action='admin_change', target=m.user,
                detail=f'관리자가 리더 권한 해제'
            )
            m.role = 'member'; m.save(); count += 1
        self.message_user(request, f'✅ {count}명 리더 권한 해제')


@admin.register(GroupLeaderLog)
class GroupLeaderLogAdmin(admin.ModelAdmin):
    list_display    = ('created_at', 'group', 'actor', 'action', 'target', 'detail')
    list_filter     = ('action',)
    search_fields   = ('group__name', 'actor__nickname', 'target__nickname')
    raw_id_fields   = ('group', 'actor', 'target')
    list_per_page   = 30
    readonly_fields = ('created_at',)
    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(GroupDissolveVote)
class GroupDissolveVoteAdmin(admin.ModelAdmin):
    list_display    = ('group', 'started_by', 'started_at', 'ends_at', 'oppose_status')
    search_fields   = ('group__name',)
    raw_id_fields   = ('group', 'started_by')
    list_per_page   = 20
    readonly_fields = ('started_at',)

    def oppose_status(self, obj):
        total  = obj.group.member_count()
        oppose = obj.oppose_count()
        needed = total // 2 + 1
        return format_html('<b>{}</b> / {} (과반 {}명)', oppose, total, needed)
    oppose_status.short_description = '반대 현황'


# ════════════════════════════════════════════════════════════════
# 🏃 봉사/활동 관리
# ════════════════════════════════════════════════════════════════
@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display    = ('title', 'creator', 'status_badge', 'is_confirmed',
                       'scheduled_at', 'participant_count', 'avg_rating', 'created_at')
    list_filter     = ('status', 'is_confirmed', 'scheduled_at')
    search_fields   = ('title', 'creator__nickname', 'location')
    raw_id_fields   = ('creator', 'confirmed_by', 'group')
    list_editable   = ('is_confirmed',)
    list_per_page   = 20
    readonly_fields = ('created_at', 'updated_at', 'avg_rating', 'rating_count',
                       'confirmed_by', 'confirmed_at')
    date_hierarchy  = 'scheduled_at'
    actions         = ['confirm_meetups', 'cancel_meetups']

    fieldsets = (
        ('기본 정보', {'fields': ('title', 'description', 'location', 'creator', 'group')}),
        ('일정', {'fields': ('scheduled_at', 'duration_hours', 'max_participants')}),
        ('상태', {'fields': ('status', 'is_confirmed', 'confirmed_by', 'confirmed_at')}),
        ('평가', {'fields': ('avg_rating', 'rating_count')}),
        ('기록', {'fields': ('created_at', 'updated_at')}),
    )

    def status_badge(self, obj):
        colors = {'planned':'#3b82f6','recruiting':'#1a7a4a','confirmed':'#D4B26A',
                  'completed':'#6b7280','cancelled':'#ef4444'}
        labels = {'planned':'계획중','recruiting':'모집중','confirmed':'확정',
                  'completed':'완료','cancelled':'취소'}
        return format_html('<span style="color:{};font-weight:700;">{}</span>',
                           colors.get(obj.status,'#6b7280'), labels.get(obj.status, obj.status))
    status_badge.short_description = '상태'
    status_badge.admin_order_field = 'status'

    def participant_count(self, obj):
        cnt = obj.participants.count()
        mx  = obj.max_participants or '∞'
        return format_html('<b>{}</b> / {}', cnt, mx)
    participant_count.short_description = '참가자'

    @admin.action(description='✅ 봉사활동 승인')
    def confirm_meetups(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_confirmed=True, status='recruiting',
                        confirmed_by=request.user, confirmed_at=timezone.now())
        self.message_user(request, f"✅ {queryset.count()}개 승인 완료")

    @admin.action(description='❌ 봉사활동 취소')
    def cancel_meetups(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"❌ {queryset.count()}개 취소 처리")


@admin.register(MeetupRating)
class MeetupRatingAdmin(admin.ModelAdmin):
    list_display    = ('meetup', 'rater', 'score_stars', 'short_comment', 'created_at')
    list_filter     = ('score',)
    search_fields   = ('meetup__title', 'rater__nickname')
    raw_id_fields   = ('meetup', 'rater')
    list_per_page   = 30
    readonly_fields = ('created_at',)

    def score_stars(self, obj):
        return '⭐' * obj.score
    score_stars.short_description = '평점'

    def short_comment(self, obj):
        return (obj.comment[:30] + '…') if obj.comment and len(obj.comment) > 30 else (obj.comment or '-')
    short_comment.short_description = '한마디'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display  = ('name', 'activity_type', 'base_points', 'points_per_hour', 'is_active')
    list_filter   = ('activity_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('base_points', 'points_per_hour', 'is_active')
    list_per_page = 20


@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display    = ('user', 'activity', 'status_badge', 'points_earned',
                       'duration_hours', 'approved_by', 'submitted_at')
    list_filter     = ('status', 'activity', 'submitted_at')
    search_fields   = ('user__nickname', 'user__username', 'description')
    raw_id_fields   = ('user', 'activity', 'approved_by')
    list_per_page   = 30
    readonly_fields = ('submitted_at', 'approved_at', 'approved_by', 'points_earned')
    date_hierarchy  = 'submitted_at'
    actions         = ['approve_proofs', 'reject_proofs']

    fieldsets = (
        ('신청 정보', {'fields': ('user', 'activity', 'description', 'proof_image', 'duration_hours')}),
        ('처리 결과', {'fields': ('status', 'points_earned', 'approved_by', 'approved_at', 'reject_reason')}),
        ('기록', {'fields': ('submitted_at',)}),
    )

    def status_badge(self, obj):
        colors = {'pending':'#f59e0b','approved':'#1a7a4a','rejected':'#ef4444'}
        labels = {'pending':'⏳ 대기','approved':'✅ 승인','rejected':'❌ 반려'}
        return format_html('<span style="color:{};font-weight:700;">{}</span>',
                           colors.get(obj.status,'#6b7280'), labels.get(obj.status, obj.status))
    status_badge.short_description = '상태'
    status_badge.admin_order_field = 'status'

    @admin.action(description='✅ 선택 활동 인증 승인')
    def approve_proofs(self, request, queryset):
        from django.utils import timezone
        from hello_world.core.views import _auto_award_badges
        count = 0
        for proof in queryset.filter(status='pending'):
            points = int(proof.activity.base_points +
                         proof.activity.points_per_hour * proof.duration_hours)
            proof.status       = 'approved'
            proof.points_earned = points
            proof.approved_at  = timezone.now()
            proof.approved_by  = request.user
            proof.save()
            proof.user.mileage_points += points
            proof.user.save(update_fields=['mileage_points'])
            try:
                _auto_award_badges(proof.user)
            except Exception:
                pass
            count += 1
        self.message_user(request, f"✅ {count}건 승인 + 포인트 적립 완료")

    @admin.action(description='❌ 선택 활동 인증 반려')
    def reject_proofs(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"❌ {count}건 반려 완료")


# ════════════════════════════════════════════════════════════════
# 📅 캘린더 관리
# ════════════════════════════════════════════════════════════════
@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display    = ('title', 'event_type', 'creator', 'group',
                       'visibility_badge', 'start_time', 'is_approved')
    list_filter     = ('event_type', 'visibility', 'is_approved', 'start_time')
    search_fields   = ('title', 'creator__username', 'creator__nickname', 'location')
    raw_id_fields   = ('creator', 'group', 'approved_by')
    list_per_page   = 30
    readonly_fields = ('created_at', 'approved_at', 'group_approved_at')
    date_hierarchy  = 'start_time'
    actions         = ['approve_public', 'approve_group', 'reject_events']

    fieldsets = (
        ('일정 정보', {'fields': ('title', 'description', 'event_type', 'location', 'color', 'all_day')}),
        ('시간', {'fields': ('start_time', 'end_time', 'rrule', 'recur_interval')}),
        ('공개 설정', {'fields': ('creator', 'group', 'visibility', 'is_approved')}),
        ('관리자 승인', {'fields': ('approved_by', 'approved_at')}),
        ('소모임장 승인', {'fields': ('group_approved_by', 'group_approved_at')}),
        ('기록', {'fields': ('created_at',)}),
    )

    def visibility_badge(self, obj):
        colors = {
            'private':'#6b7280','group_pending':'#f59e0b',
            'group':'#D4B26A','pending':'#f59e0b','public':'#1a7a4a'
        }
        labels = {
            'private':'🔒나만','group_pending':'⏳소모임대기',
            'group':'👥소모임','pending':'⏳전체대기','public':'🏘전체공개'
        }
        return format_html('<span style="color:{};font-weight:700;">{}</span>',
                           colors.get(obj.visibility,'#6b7280'),
                           labels.get(obj.visibility, obj.visibility))
    visibility_badge.short_description = '공개범위'
    visibility_badge.admin_order_field = 'visibility'

    @admin.action(description='✅ 전체 공개 승인')
    def approve_public(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(visibility='pending').update(
            is_approved=True, visibility='public',
            approved_by=request.user, approved_at=timezone.now()
        )
        self.message_user(request, f"✅ {count}개 전체 공개 승인 완료")

    @admin.action(description='✅ 소모임 공개 승인')
    def approve_group(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(visibility='group_pending').update(
            is_approved=True, visibility='group',
            group_approved_by=request.user, group_approved_at=timezone.now()
        )
        self.message_user(request, f"✅ {count}개 소모임 공개 승인 완료")

    @admin.action(description='❌ 일정 승인 거부 (나만보기로)')
    def reject_events(self, request, queryset):
        count = queryset.filter(
            visibility__in=['pending','group_pending']
        ).update(visibility='private', is_approved=False)
        self.message_user(request, f"❌ {count}개 거부 (나만보기로 변경)")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display    = ('post', 'start_time', 'end_time', 'location', 'created_at')
    list_filter     = ('start_time',)
    search_fields   = ('post__title', 'location')
    list_per_page   = 20
    readonly_fields = ('created_at',)


# ════════════════════════════════════════════════════════════════
# 📊 운영 관리
# ════════════════════════════════════════════════════════════════
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display    = ('title', 'creator', 'status_badge', 'survey_type',
                       'response_count', 'created_at')
    list_filter     = ('status', 'survey_type', 'created_at')
    search_fields   = ('title', 'creator__nickname')
    raw_id_fields   = ('creator',)
    list_per_page   = 20
    readonly_fields = ('created_at',)
    actions         = ['close_surveys']

    def status_badge(self, obj):
        colors = {'active':'#1a7a4a','closed':'#6b7280','draft':'#f59e0b'}
        labels = {'active':'✅ 진행중','closed':'🔒 종료','draft':'📝 초안'}
        return format_html('<span style="color:{};font-weight:700;">{}</span>',
                           colors.get(obj.status,'#6b7280'), labels.get(obj.status, obj.status))
    status_badge.short_description = '상태'

    def response_count(self, obj):
        return format_html('<b>{}명</b>', obj.responses.count())
    response_count.short_description = '참여수'

    @admin.action(description='🔒 선택 설문 종료')
    def close_surveys(self, request, queryset):
        count = queryset.filter(status='active').update(status='closed')
        self.message_user(request, f"🔒 {count}개 설문 종료")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display    = ('recipient', 'notification_type', 'short_message',
                       'is_read_icon', 'created_at')
    list_filter     = ('notification_type', 'is_read', 'created_at')
    search_fields   = ('recipient__nickname', 'title', 'message')
    raw_id_fields   = ('recipient',)
    list_per_page   = 30
    readonly_fields = ('created_at',)
    date_hierarchy  = 'created_at'
    actions         = ['mark_read', 'delete_old']

    def short_message(self, obj):
        msg = obj.message or obj.title or ''
        return (msg[:40] + '…') if len(msg) > 40 else msg
    short_message.short_description = '메시지'

    def is_read_icon(self, obj):
        return format_html('<span style="color:#1a7a4a;">✅</span>') if obj.is_read \
               else format_html('<span style="color:#f59e0b;">🔔</span>')
    is_read_icon.short_description = '읽음'
    is_read_icon.admin_order_field = 'is_read'

    @admin.action(description='✅ 읽음 처리')
    def mark_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"✅ {count}개 읽음 처리")

    @admin.action(description='🗑 30일 이상 된 알림 삭제')
    def delete_old(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=30)
        count = queryset.filter(created_at__lt=cutoff, is_read=True).delete()[0]
        self.message_user(request, f"🗑 {count}개 삭제 완료")


# ════════════════════════════════════════════════════════════════
# ⚙️ 시스템 설정
# ════════════════════════════════════════════════════════════════
@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display    = ('site_name', 'hero_color', 'updated_at')
    fields          = ('site_name', 'hero_color', 'hero_image')
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = SiteConfig.objects.get_or_create(id=1)
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:core_siteconfig_change', args=[obj.pk]))


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display    = ('created_at', 'admin', 'action_badge', 'target_user', 'detail', 'ip_address')
    list_filter     = ('action', 'created_at')
    search_fields   = ('admin__nickname', 'target_user__nickname', 'detail')
    ordering        = ('-created_at',)
    list_per_page   = 30
    readonly_fields = ('admin', 'target_user', 'action', 'detail', 'ip_address', 'created_at')
    date_hierarchy  = 'created_at'

    def action_badge(self, obj):
        colors = {'verify':'#1a7a4a','activate':'#3b82f6','deactivate':'#ef4444',
                  'pw_reset':'#f59e0b','admin_change':'#8b5cf6'}
        color = colors.get(obj.action, '#6b7280')
        return format_html('<span style="color:{};font-weight:700;">{}</span>', color, obj.action)
    action_badge.short_description = '액션'

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# ════════════════════════════════════════════════════════════════
# 대시보드 통계 주입 (AdminSite.index 오버라이드)
# ════════════════════════════════════════════════════════════════
from django.contrib.admin import AdminSite as _AdminSite

_orig_index = _AdminSite.index

def _patched_index(self, request, extra_context=None):
    from .models import CustomUser, Post, Group, ActivityProof, Survey, Notification, CalendarEvent, Meetup
    from django.utils import timezone
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    extra_context = extra_context or {}
    extra_context.update({
        'stat_total_users':      CustomUser.objects.filter(is_active=True).count(),
        'stat_unverified':       CustomUser.objects.filter(is_verified=False, is_active=True).count(),
        'stat_new_users_week':   CustomUser.objects.filter(date_joined__gte=week_ago).count(),
        'stat_total_posts':      Post.objects.filter(is_active=True).count(),
        'stat_pending_proofs':   ActivityProof.objects.filter(status='pending').count(),
        'stat_pending_groups':   Group.objects.filter(status='pending').count(),
        'stat_pending_calendar': CalendarEvent.objects.filter(visibility__in=['pending','group_pending']).count(),
        'stat_pending_meetups':  Meetup.objects.filter(is_confirmed=False, status='planned').count(),
        'stat_active_surveys':   Survey.objects.filter(status='active').count(),
        'stat_unread_noti':      Notification.objects.filter(is_read=False).count(),
        'recent_users':          CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:5],
        'pending_proofs':        ActivityProof.objects.filter(status='pending').select_related('user','activity').order_by('-submitted_at')[:5],
        'pending_groups':        Group.objects.filter(status='pending').select_related('creator').order_by('-created_at')[:5],
        'pending_calendar':      CalendarEvent.objects.filter(visibility__in=['pending','group_pending']).select_related('creator','group').order_by('-created_at')[:5],
    })
    return _orig_index(self, request, extra_context)

_AdminSite.index = _patched_index
