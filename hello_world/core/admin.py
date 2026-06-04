from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.core.mail import send_mail
import random, string
from .models import (
    AdminActionLog,
    CustomUser, Badge, UserBadge, UserFollow,
    Activity, ActivityProof,
    Rating, Board, Post, Comment, ManagementDocument,
    Event, Notification,
    Group, GroupMember, GroupLeaderLog, GroupDissolveVote,
    MemberGrade, BoardGradePermission,
    Survey,
    CalendarEvent,
    SiteConfig,
)

# ════════════════════════════════════════════════════
# 사이트 기본 설정
# ════════════════════════════════════════════════════
admin.site.site_header = '🌿 해솔마을 7단지 지킴이 관리자'
admin.site.site_title  = '해솔7 관리자'
admin.site.index_title = '📋 관리 메뉴 — 모든 관리 행위는 자동으로 기록됩니다'

def _get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR')

def _log(admin_user, target, action, detail, ip):
    AdminActionLog.objects.create(
        admin=admin_user, target_user=target,
        action=action, detail=detail, ip_address=ip
    )


# ════════════════════════════════════════════════════
# 👥 회원 관리
# ════════════════════════════════════════════════════
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'nickname', 'dong_ho', 'email',
                      'is_verified', 'is_active', 'is_staff', 'date_joined')
    list_filter   = ('is_verified', 'is_staff', 'is_active', 'groups')
    search_fields = ('username', 'nickname', 'dong', 'ho', 'email')
    ordering      = ('-date_joined',)
    list_per_page = 30
    actions       = ['action_verify', 'action_unverify',
                     'action_activate', 'action_deactivate',
                     'action_send_temp_password']

    fieldsets = UserAdmin.fieldsets + (
        ('🏠 입주민 정보', {'fields': (
            'nickname', 'dong', 'ho', 'unit_number', 'phone_number'
        )}),
        ('🔐 보안 질문', {'fields': (
            'security_question', 'security_answer'
        ), 'classes': ('collapse',)}),
        ('🏅 활동 및 포인트', {'fields': (
            'mileage_points', 'manners_score', 'is_verified', 'current_badges'
        )}),
    )

    def dong_ho(self, obj):
        return f"{obj.dong}동 {obj.ho}호" if obj.dong else "-"
    dong_ho.short_description = '동/호수'

    @admin.action(description='✅ 입주민 인증 승인')
    def action_verify(self, request, queryset):
        ip = _get_client_ip(request)
        count = queryset.filter(is_verified=False).update(is_verified=True)
        for user in queryset:
            _log(request.user, user, 'verify', '입주민 인증 승인', ip)
        self.message_user(request, f"✅ {count}명 인증 승인 완료")

    @admin.action(description='❌ 입주민 인증 취소')
    def action_unverify(self, request, queryset):
        ip = _get_client_ip(request)
        count = queryset.filter(is_verified=True).update(is_verified=False)
        for user in queryset:
            _log(request.user, user, 'verify', '입주민 인증 취소', ip)
        self.message_user(request, f"❌ {count}명 인증 취소 완료")

    @admin.action(description='🟢 선택 계정 활성화')
    def action_activate(self, request, queryset):
        ip = _get_client_ip(request)
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=False):
            user.is_active = True
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'activate', '', ip)
            count += 1
        self.message_user(request, f"🟢 {count}명 활성화 완료")

    @admin.action(description='🔴 선택 계정 비활성화 (최고관리자 제외)')
    def action_deactivate(self, request, queryset):
        ip = _get_client_ip(request)
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=True):
            user.is_active = False
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'deactivate', '', ip)
            count += 1
        self.message_user(request, f"🔴 {count}명 비활성화 완료")

    @admin.action(description='🔑 임시 비밀번호 발급 및 이메일 발송')
    def action_send_temp_password(self, request, queryset):
        ip = _get_client_ip(request)
        ok_list, fail_list = [], []
        for user in queryset:
            if user.is_superuser:
                continue
            if not user.email:
                fail_list.append(f"{user.nickname or user.username}(이메일 없음)")
                continue
            tmp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(tmp_pw)
            user.save(update_fields=['password'])
            try:
                send_mail(
                    subject='[해솔7 지킴이] 임시 비밀번호 발급',
                    message=(
                        f"{user.nickname or user.username}님,\n\n"
                        f"임시 비밀번호: {tmp_pw}\n\n"
                        f"로그인 후 즉시 변경해주세요.\n"
                        f"변경: {request.scheme}://{request.get_host()}/mypage/edit/"
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                )
                ok_list.append(user.nickname or user.username)
                _log(request.user, user, 'pw_reset', f"이메일:{user.email[:3]}***", ip)
            except Exception as e:
                fail_list.append(f"{user.nickname or user.username}(발송실패)")
        if ok_list:
            self.message_user(request, f"✅ 발송완료: {', '.join(ok_list)}", messages.SUCCESS)
        if fail_list:
            self.message_user(request, f"⚠ 실패: {', '.join(fail_list)}", messages.WARNING)


@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'order', 'required_points', 'required_activities',
                      'badge_color', 'is_active')
    list_editable = ('required_points', 'required_activities', 'order', 'is_active')
    ordering      = ('order',)
    list_per_page = 10


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'required_points',
                      'required_activities', 'is_active')
    list_filter   = ('category', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('required_points', 'required_activities', 'is_active')
    list_per_page = 20


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'badge', 'earned_at', 'is_displayed')
    list_filter   = ('badge', 'is_displayed')
    search_fields = ('user__nickname', 'user__username', 'badge__title')
    raw_id_fields = ('user', 'badge')
    list_per_page = 30


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display    = ('follower', 'following', 'created_at')
    search_fields   = ('follower__nickname', 'following__nickname')
    raw_id_fields   = ('follower', 'following')
    list_per_page   = 30
    readonly_fields = ('created_at',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display    = ('rater', 'rated_user', 'score', 'short_comment', 'created_at')
    list_filter     = ('score',)
    search_fields   = ('rater__nickname', 'rated_user__nickname', 'comment')
    raw_id_fields   = ('rater', 'rated_user')
    list_per_page   = 30
    readonly_fields = ('created_at',)

    def short_comment(self, obj):
        if obj.comment:
            return obj.comment[:30] + '...' if len(obj.comment) > 30 else obj.comment
        return '-'
    short_comment.short_description = '한마디'


# ════════════════════════════════════════════════════
# 📋 게시판
# ════════════════════════════════════════════════════
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display  = ('name', 'board_type', 'layout_type', 'order',
                      'write_permission', 'is_active')
    list_editable = ('order', 'layout_type', 'is_active')
    search_fields = ('name',)
    list_per_page = 20


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display    = ('title', 'author', 'board', 'view_count',
                        'like_count', 'is_pinned', 'is_active', 'created_at')
    list_filter     = ('board', 'is_active', 'is_pinned')
    search_fields   = ('title', 'content', 'author__nickname')
    raw_id_fields   = ('author', 'board')
    list_editable   = ('is_pinned', 'is_active')
    list_per_page   = 30
    readonly_fields = ('created_at', 'view_count')
    actions         = ['pin_posts', 'unpin_posts', 'hide_posts']

    @admin.action(description='📌 선택 게시글 상단 고정')
    def pin_posts(self, request, queryset):
        queryset.update(is_pinned=True)
        self.message_user(request, f"📌 {queryset.count()}개 고정 완료")

    @admin.action(description='📌 선택 게시글 고정 해제')
    def unpin_posts(self, request, queryset):
        queryset.update(is_pinned=False)
        self.message_user(request, f"✅ {queryset.count()}개 고정 해제")

    @admin.action(description='🚫 선택 게시글 숨김 처리')
    def hide_posts(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"🚫 {queryset.count()}개 숨김 처리 완료")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ('author', 'post', 'short_content', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('content', 'author__nickname')
    raw_id_fields = ('author', 'post')
    list_editable = ('is_active',)
    list_per_page = 30

    def short_content(self, obj):
        return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
    short_content.short_description = '내용 미리보기'


@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    list_display    = ('title', 'category', 'author', 'view_count',
                        'has_file', 'is_active', 'created_at')
    list_filter     = ('category', 'is_active')
    search_fields   = ('title', 'content')
    list_editable   = ('is_active',)
    raw_id_fields   = ('author',)
    list_per_page   = 20
    readonly_fields = ('created_at', 'updated_at', 'view_count')

    def has_file(self, obj):
        return format_html('<span style="color:green;">📎</span>') if obj.file else '-'
    has_file.short_description = '첨부'


# ════════════════════════════════════════════════════
# 🤝 소모임
# ════════════════════════════════════════════════════
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'group_type', 'join_type', 'status',
                      'member_count_display', 'emblem_level', 'is_active', 'created_at')
    list_filter   = ('group_type', 'join_type', 'status', 'is_active')
    search_fields = ('name', 'description', 'creator__nickname')
    raw_id_fields = ('creator',)
    list_editable = ('status', 'is_active')
    list_per_page = 20
    actions       = ['approve_groups']

    def member_count_display(self, obj):
        return format_html('<b>{}</b>명', obj.member_count())
    member_count_display.short_description = '회원수'

    @admin.action(description='✅ 선택 소모임 승인 (10인 이상 대기중)')
    def approve_groups(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='active', approved_by=request.user, approved_at=timezone.now()
        )
        self.message_user(request, f"✅ {count}개 소모임 승인 완료")


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display  = ('user', 'group', 'role', 'join_status', 'joined_at')
    list_filter   = ('role', 'join_status')
    search_fields = ('user__nickname', 'group__name')
    raw_id_fields = ('user', 'group')
    list_editable = ('join_status',)
    list_per_page = 30


@admin.register(GroupLeaderLog)
class GroupLeaderLogAdmin(admin.ModelAdmin):
    list_display    = ('created_at', 'group', 'actor', 'action', 'target', 'detail')
    list_filter     = ('action',)
    search_fields   = ('group__name', 'actor__nickname')
    raw_id_fields   = ('group', 'actor', 'target')
    list_per_page   = 30
    readonly_fields = ('created_at',)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(GroupDissolveVote)
class GroupDissolveVoteAdmin(admin.ModelAdmin):
    list_display    = ('group', 'started_by', 'started_at', 'ends_at', 'oppose_count_display')
    search_fields   = ('group__name',)
    raw_id_fields   = ('group', 'started_by')
    list_per_page   = 20
    readonly_fields = ('started_at',)

    def oppose_count_display(self, obj):
        total = obj.group.member_count()
        oppose = obj.oppose_count()
        return format_html('<b>{}</b> / {} (과반: {})', oppose, total, total // 2 + 1)
    oppose_count_display.short_description = '반대 현황'


# ════════════════════════════════════════════════════
# 📅 활동/캘린더
# ════════════════════════════════════════════════════
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display  = ('name', 'activity_type', 'base_points', 'points_per_hour', 'is_active')
    list_filter   = ('activity_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('base_points', 'points_per_hour', 'is_active')
    list_per_page = 20


@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display    = ('user', 'activity', 'status', 'points_earned', 'submitted_at')
    list_filter     = ('status', 'activity')
    search_fields   = ('user__nickname', 'user__username')
    list_editable   = ('status',)
    raw_id_fields   = ('user', 'activity')
    list_per_page   = 30
    readonly_fields = ('submitted_at',)
    actions         = ['approve_selected', 'reject_selected']

    @admin.action(description='✅ 선택 활동 인증 승인')
    def approve_selected(self, request, queryset):
        queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f"✅ 승인 완료")

    @admin.action(description='❌ 선택 활동 인증 반려')
    def reject_selected(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"❌ 반려 완료")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display    = ('post', 'start_time', 'end_time', 'location', 'created_at')
    list_filter     = ('start_time',)
    search_fields   = ('post__title', 'location')
    list_per_page   = 20
    readonly_fields = ('created_at',)


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display  = ('title', 'event_type', 'start_time', 'creator',
                      'visibility', 'is_approved')
    list_filter   = ('event_type', 'visibility', 'is_approved')
    search_fields = ('title', 'creator__username')
    list_editable = ('is_approved',)
    actions       = ['approve_events']

    @admin.action(description='✅ 선택 일정 승인')
    def approve_events(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, visibility='public',
                        approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}개 승인 완료')


# ════════════════════════════════════════════════════
# 📊 설문/알림
# ════════════════════════════════════════════════════
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display    = ('title', 'creator', 'status', 'survey_type',
                        'response_count_display', 'created_at')
    list_filter     = ('status', 'survey_type')
    search_fields   = ('title', 'creator__nickname')
    raw_id_fields   = ('creator',)
    list_per_page   = 20
    readonly_fields = ('created_at',)

    def response_count_display(self, obj):
        return format_html('<b>{}</b>명', obj.responses.count())
    response_count_display.short_description = '참여수'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display    = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter     = ('notification_type', 'is_read')
    search_fields   = ('recipient__nickname', 'title', 'message')
    raw_id_fields   = ('recipient',)
    list_per_page   = 30
    readonly_fields = ('created_at',)
    actions         = ['mark_all_read']

    @admin.action(description='✅ 선택 알림 읽음 처리')
    def mark_all_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"✅ {queryset.count()}개 읽음 처리")


# ════════════════════════════════════════════════════
# ⚙️ 사이트 설정 / 로그
# ════════════════════════════════════════════════════
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
    list_display    = ('created_at', 'admin', 'action', 'target_user', 'detail', 'ip_address')
    list_filter     = ('action',)
    search_fields   = ('admin__nickname', 'target_user__nickname', 'detail')
    ordering        = ('-created_at',)
    list_per_page   = 30
    readonly_fields = ('admin', 'target_user', 'action', 'detail', 'ip_address', 'created_at')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


# ════════════════════════════════════════════════════
# 커스텀 AdminSite — 대시보드 통계
# ════════════════════════════════════════════════════
from django.contrib.admin import AdminSite as BaseAdminSite

class HaesolAdminSite(BaseAdminSite):
    def index(self, request, extra_context=None):
        from .models import CustomUser, Post, Group, ActivityProof, CalendarEvent, Survey
        extra_context = extra_context or {}
        extra_context.update({
            'stat_total_users':    CustomUser.objects.filter(is_active=True).count(),
            'stat_unverified':     CustomUser.objects.filter(is_verified=False, is_active=True).count(),
            'stat_pending_proofs': ActivityProof.objects.filter(status='pending').count(),
            'stat_pending_groups': Group.objects.filter(status='pending').count(),
            'stat_total_posts':    Post.objects.filter(is_active=True).count(),
            'stat_active_surveys': Survey.objects.filter(status='active').count(),
        })
        return super().index(request, extra_context)

