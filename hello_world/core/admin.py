from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.core.mail import send_mail
import random, string
from .models import (
    AdminActionLog,
    CustomUser, Badge, UserBadge,
    Activity, ActivityProof, ActivityVerification,
    Rating, Board, Category, Post, PostImage, Comment, PostLike,
    Event, Notification, ManagementDocument,
    Group, GroupMember, GroupPost, GroupComment, GroupChat,
    MemberGrade, BoardGradePermission,
    Survey, SurveyQuestion, SurveyResponse,
    PublicChat, DirectMessage, ChatHistory, ChatPoll,
    CalendarEvent,
    SiteConfig,
)

# ════════════════════════════════════════════════════════════════════
# 사이트 기본 설정
# ════════════════════════════════════════════════════════════════════
admin.site.site_header  = '🌿 해솔마을 7단지 지킴이 관리자'
admin.site.site_title   = '해솔7 관리자'
admin.site.index_title  = '📋 관리 메뉴 — 모든 관리 행위는 자동으로 기록됩니다'


# ── 공통 유틸 ────────────────────────────────────────────────────────
def _get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR')

def _log(admin_user, target, action, detail, ip):
    """관리자 행위 로그 — 개인정보보호법 29조"""
    AdminActionLog.objects.create(
        admin=admin_user, target_user=target,
        action=action, detail=detail, ip_address=ip
    )


# ════════════════════════════════════════════════════════════════════
# 👤 회원 관리
# ════════════════════════════════════════════════════════════════════
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """입주민 계정 관리 — 등급 변경·임시 비밀번호 발급·계정 활성화 가능"""
    list_display   = ('username', 'nickname', 'dong_ho', 'email_display',
                       'grade_display', 'mileage_points', 'is_verified',
                       'is_active', 'date_joined')
    list_filter    = ('is_verified', 'is_staff', 'is_active', 'groups')
    search_fields  = ('username', 'nickname', 'dong', 'ho', 'email')
    ordering       = ('-date_joined',)
    list_per_page  = 30
    actions        = ['action_send_temp_password', 'action_activate', 'action_deactivate']

    fieldsets = UserAdmin.fieldsets + (
        ('🏠 입주민 정보', {'fields': ('nickname', 'dong', 'ho', 'unit_number', 'phone_number')}),
        ('🔐 보안 질문 (비밀번호 찾기용)', {'fields': ('security_question', 'security_answer')}),
        ('🏅 활동 및 포인트', {'fields': ('mileage_points', 'manners_score',
                                          'is_verified', 'current_badges')}),
    )

    def dong_ho(self, obj):
        return f"{obj.dong}동 {obj.ho}호" if obj.dong else "-"
    dong_ho.short_description = '동/호수'

    def email_display(self, obj):
        if obj.email:
            return format_html('<span style="color:#1a7a4a;">✓</span> {}', obj.email[:4] + '***')
        return format_html('<span style="color:#e53935;font-size:0.85em;">⚠ 미등록</span>')
    email_display.short_description = '이메일'

    def grade_display(self, obj):
        groups = obj.groups.all()
        if groups:
            return format_html(
                '<span style="background:#e8f5ee;color:#1a7a4a;'                'padding:2px 8px;border-radius:10px;font-size:0.8em;">{}</span>',
                groups[0].name
            )
        return format_html('<span style="color:#ccc;font-size:0.8em;">미배정</span>')
    grade_display.short_description = '등급'

    @admin.action(description='🔑 임시 비밀번호 발급 — 이메일로 자동 발송 (개인정보 로그 기록됨)')
    def action_send_temp_password(self, request, queryset):
        """선택한 회원에게 임시 비밀번호를 이메일로 발송합니다.
        평문 비밀번호는 서버에 저장되지 않으며, 모든 행위는 로그에 기록됩니다."""
        ip = _get_client_ip(request)
        ok_list, fail_list = [], []

        for user in queryset:
            if user.is_superuser:
                self.message_user(request,
                    f"⛔ {user.username}: 최고관리자 계정은 변경할 수 없습니다.",
                    level=messages.ERROR)
                continue
            if not user.email:
                fail_list.append(f"{user.nickname or user.username}(이메일 미등록)")
                continue

            tmp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(tmp_pw)
            user.save(update_fields=['password'])

            try:
                send_mail(
                    subject='[해솔7 지킴이] 임시 비밀번호가 발급됐어요',
                    message=(
                        f"{user.nickname or user.username}님, 안녕하세요.\n\n"
                        f"관리자가 회원님의 비밀번호를 초기화했습니다.\n\n"
                        f"  임시 비밀번호: {tmp_pw}\n\n"
                        f"보안을 위해 로그인 후 즉시 비밀번호를 변경해주세요.\n"
                        f"비밀번호 변경: {request.scheme}://{request.get_host()}/mypage/edit/\n\n"
                        f"본인이 요청하지 않은 경우 즉시 관리자에게 문의해주세요.\n\n"
                        f"해솔7 지킴이 드림"
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                ok_list.append(user.nickname or user.username)
                _log(request.user, user, 'pw_reset',
                     f"이메일 발송 성공 | 수신: {user.email[:3]}***", ip)
            except Exception as e:
                fail_list.append(f"{user.nickname or user.username}(발송 실패)")
                _log(request.user, user, 'pw_reset',
                     f"이메일 발송 실패: {str(e)[:50]}", ip)

        if ok_list:
            self.message_user(request,
                f"✅ 임시 비밀번호 발송 완료: {', '.join(ok_list)}", level=messages.SUCCESS)
        if fail_list:
            self.message_user(request,
                f"⚠ 발송 실패 (이메일 확인 필요): {', '.join(fail_list)}", level=messages.WARNING)

    @admin.action(description='✅ 선택 계정 활성화 — 로그인 허용')
    def action_activate(self, request, queryset):
        ip = _get_client_ip(request)
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=False):
            user.is_active = True
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'activate', '', ip)
            count += 1
        self.message_user(request, f"✅ {count}명 활성화 완료")

    @admin.action(description='🚫 선택 계정 비활성화 — 로그인 차단 (최고관리자 제외)')
    def action_deactivate(self, request, queryset):
        ip = _get_client_ip(request)
        protected = queryset.filter(is_superuser=True).count()
        count = 0
        for user in queryset.filter(is_superuser=False, is_active=True):
            user.is_active = False
            user.save(update_fields=['is_active'])
            _log(request.user, user, 'deactivate', '', ip)
            count += 1
        if protected:
            self.message_user(request,
                f"⛔ 최고관리자 {protected}명은 보호되어 변경되지 않았습니다.",
                level=messages.WARNING)
        self.message_user(request, f"🚫 {count}명 비활성화 완료")


# ════════════════════════════════════════════════════════════════════
# 🏅 배지 관리
# ════════════════════════════════════════════════════════════════════
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """봉사 활동 달성 시 자동 지급되는 배지를 관리합니다"""
    list_display   = ('title', 'category_display', 'required_points',
                       'required_activities', 'is_active', 'status_display')
    list_filter    = ('category', 'is_active')
    search_fields  = ('title', 'description')
    list_editable  = ('required_points', 'required_activities', 'is_active')
    list_per_page  = 20

    def category_display(self, obj):
        colors = {'security': 'primary', 'environment': 'success',
                  'community': 'info', 'helping': 'warning'}
        color  = colors.get(obj.category, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_category_display())
    category_display.short_description = '카테고리'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 활성</span>')
        return format_html('<span style="color:red;">● 비활성</span>')
    status_display.short_description = '상태'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """회원이 획득한 배지 목록입니다"""
    list_display   = ('user', 'badge', 'earned_at', 'is_displayed')
    list_filter    = ('badge', 'is_displayed')
    search_fields  = ('user__nickname', 'user__username', 'badge__title')
    raw_id_fields  = ('user', 'badge')
    list_per_page  = 30


# ════════════════════════════════════════════════════════════════════
# 🤝 봉사활동 관리
# ════════════════════════════════════════════════════════════════════
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """봉사활동 종류와 포인트 기준을 설정합니다"""
    list_display   = ('name', 'activity_type', 'base_points',
                       'points_per_hour', 'is_active')
    list_filter    = ('activity_type', 'is_active')
    search_fields  = ('name', 'description')
    list_editable  = ('base_points', 'points_per_hour', 'is_active')
    list_per_page  = 20


@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    """입주민이 제출한 봉사 활동 인증 신청을 승인·반려합니다"""
    list_display   = ('user', 'activity', 'status_display', 'status',
                       'points_earned', 'submitted_at')
    list_filter    = ('status', 'activity')
    search_fields  = ('user__nickname', 'user__username')
    list_editable  = ('status',)
    actions        = ['approve_selected', 'reject_selected']
    raw_id_fields  = ('user', 'activity')
    list_per_page  = 30
    readonly_fields = ('submitted_at',)

    def status_display(self, obj):
        colors = {'pending': 'orange', 'approved': 'green', 'rejected': 'red'}
        labels = {'pending': '⏳ 검토 대기', 'approved': '✅ 승인됨', 'rejected': '❌ 반려됨'}
        return format_html('<span style="color:{};">{}</span>',
            colors.get(obj.status, 'gray'), labels.get(obj.status, obj.status))
    status_display.short_description = '승인 상태'

    @admin.action(description='✅ 선택한 활동 인증 승인')
    def approve_selected(self, request, queryset):
        for proof in queryset.filter(status='pending'):
            proof.status = 'approved'
            proof.save()
        self.message_user(request, f"✅ {queryset.count()}건 승인 완료")

    @admin.action(description='❌ 선택한 활동 인증 반려')
    def reject_selected(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"❌ {queryset.count()}건 반려 완료")


# ════════════════════════════════════════════════════════════════════
# 📋 게시판 관리
# ════════════════════════════════════════════════════════════════════
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """게시판 목록과 공개 여부를 관리합니다. 순서(order) 숫자가 작을수록 위에 표시됩니다"""
    list_display   = ('name', 'board_type', 'order', 'is_active', 'status_display')
    list_editable  = ('order', 'is_active')
    search_fields  = ('name',)
    list_per_page  = 20

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개중</span>')
        return format_html('<span style="color:gray;">● 숨김</span>')
    status_display.short_description = '공개 상태'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """입주민이 작성한 게시글을 관리합니다. 부적절한 게시글은 비활성화로 숨길 수 있습니다"""
    list_display   = ('title', 'author', 'board', 'view_count',
                       'like_count', 'created_at', 'status_display')
    list_filter    = ('board', 'is_active')
    search_fields  = ('title', 'content', 'author__nickname')
    raw_id_fields  = ('author', 'board')
    list_per_page  = 30
    readonly_fields = ('created_at', 'view_count')

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = '좋아요 수'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개</span>')
        return format_html('<span style="color:red;">● 숨김처리됨</span>')
    status_display.short_description = '게시 상태'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """게시글 댓글을 관리합니다. 부적절한 댓글은 비활성화로 숨길 수 있습니다"""
    list_display   = ('author', 'post', 'short_content', 'created_at', 'status_display')
    list_filter    = ('is_active',)
    search_fields  = ('content', 'author__nickname')
    raw_id_fields  = ('author', 'post')
    list_per_page  = 30

    def short_content(self, obj):
        return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
    short_content.short_description = '내용 미리보기'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개</span>')
        return format_html('<span style="color:red;">● 숨김처리됨</span>')
    status_display.short_description = '게시 상태'


# ════════════════════════════════════════════════════════════════════
# 📂 관리 문서
# ════════════════════════════════════════════════════════════════════
@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    """단지 관리 규약·회의록·공문 등 공식 문서를 등록·관리합니다"""
    list_display   = ('title', 'category', 'author', 'view_count',
                       'has_file', 'is_active', 'created_at')
    list_filter    = ('category', 'is_active')
    search_fields  = ('title', 'content')
    list_editable  = ('is_active',)
    raw_id_fields  = ('author',)
    list_per_page  = 20
    readonly_fields = ('created_at', 'updated_at', 'view_count')

    def has_file(self, obj):
        if obj.file:
            return format_html('<span style="color:green;">📎 첨부됨</span>')
        return format_html('<span style="color:gray;">없음</span>')
    has_file.short_description = '첨부파일'


# ════════════════════════════════════════════════════════════════════
# ❤️ 이웃 온기 평가
# ════════════════════════════════════════════════════════════════════
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """입주민 간 온기 점수 평가 내역입니다. 부적절한 평가는 삭제할 수 있습니다"""
    list_display   = ('rater', 'rated_user', 'score_display', 'short_comment', 'created_at')
    list_filter    = ('score',)
    search_fields  = ('rater__nickname', 'rated_user__nickname', 'comment')
    raw_id_fields  = ('rater', 'rated_user')
    list_per_page  = 30
    readonly_fields = ('created_at',)

    def score_display(self, obj):
        return format_html('{}  (<b>{}점</b>)', '⭐' * obj.score, obj.score)
    score_display.short_description = '평점'

    def short_comment(self, obj):
        if obj.comment:
            return obj.comment[:30] + '...' if len(obj.comment) > 30 else obj.comment
        return '-'
    short_comment.short_description = '한마디'


# ════════════════════════════════════════════════════════════════════
# 👥 소모임 관리
# ════════════════════════════════════════════════════════════════════
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """입주민 소모임을 관리합니다. 비활성화하면 소모임이 목록에서 숨겨집니다"""
    list_display   = ('name', 'group_type', 'creator', 'member_count',
                       'status_display', 'created_at')
    list_filter    = ('group_type', 'is_active')
    search_fields  = ('name', 'description', 'creator__nickname')
    raw_id_fields  = ('creator',)
    list_per_page  = 20

    def member_count(self, obj):
        return format_html('<b>{}</b>명', obj.members.count())
    member_count.short_description = '회원 수'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 운영중</span>')
        return format_html('<span style="color:gray;">● 해산됨</span>')
    status_display.short_description = '운영 상태'


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    """소모임 회원 구성을 관리합니다"""
    list_display   = ('user', 'group', 'role_display', 'joined_at')
    list_filter    = ('role',)
    search_fields  = ('user__nickname', 'group__name')
    raw_id_fields  = ('user', 'group')
    list_per_page  = 30

    def role_display(self, obj):
        if obj.role == 'leader':
            return format_html('<span style="color:#e67e22;">👑 모임장</span>')
        return format_html('<span style="color:#27ae60;">일반 회원</span>')
    role_display.short_description = '역할'


# ════════════════════════════════════════════════════════════════════
# 📅 봉사 일정 및 통합 캘린더
# ════════════════════════════════════════════════════════════════════
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """봉사활동 일정을 등록·수정합니다"""
    list_display   = ('post', 'start_time', 'end_time', 'location', 'created_at')
    list_filter    = ('start_time',)
    search_fields  = ('post__title', 'location')
    list_per_page  = 20
    readonly_fields = ('created_at',)


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """통합 캘린더 일정을 관리합니다. 미승인 일정은 공개되지 않습니다"""
    list_display  = ('title', 'event_type', 'start_time', 'creator',
                      'visibility', 'is_approved')
    list_filter   = ('event_type', 'visibility', 'is_approved')
    search_fields = ('title', 'creator__username')
    actions       = ['approve_events']

    @admin.action(description='✅ 선택 일정 공개 승인')
    def approve_events(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, visibility='public',
                        approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}개 일정이 승인됐습니다.')


# ════════════════════════════════════════════════════════════════════
# 🔔 알림
# ════════════════════════════════════════════════════════════════════
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """회원에게 발송된 알림 내역입니다. 전체 공지 발송은 여기서 진행할 수 있습니다"""
    list_display   = ('recipient', 'title', 'type_display', 'read_display', 'created_at')
    list_filter    = ('notification_type', 'is_read')
    search_fields  = ('recipient__nickname', 'title', 'message')
    raw_id_fields  = ('recipient',)
    list_per_page  = 30
    readonly_fields = ('created_at',)

    def type_display(self, obj):
        icons = {'activity': '🤝', 'announcement': '📢', 'badge': '🏅',
                 'community': '👥', 'event': '📅', 'system': '⚙️'}
        return format_html('{} {}', icons.get(obj.notification_type, '🔔'),
                           obj.get_notification_type_display())
    type_display.short_description = '알림 종류'

    def read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color:gray;">읽음</span>')
        return format_html('<span style="color:#2563eb;font-weight:bold;">● 안읽음</span>')
    read_display.short_description = '확인 여부'


# ════════════════════════════════════════════════════════════════════
# 📊 설문조사
# ════════════════════════════════════════════════════════════════════
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    """입주민 대상 설문조사를 관리합니다. 진행 중인 설문은 결과를 실시간으로 확인할 수 있습니다"""
    list_display   = ('title', 'creator', 'status_display', 'survey_type',
                       'response_count', 'created_at')
    list_filter    = ('status', 'survey_type')
    search_fields  = ('title', 'creator__nickname')
    raw_id_fields  = ('creator',)
    list_per_page  = 20
    readonly_fields = ('created_at',)

    def status_display(self, obj):
        colors = {'draft': 'gray', 'active': 'green', 'closed': 'red'}
        labels = {'draft': '✏️ 작성중', 'active': '✅ 진행중', 'closed': '🔒 마감됨'}
        return format_html('<span style="color:{};">{}</span>',
            colors.get(obj.status, 'gray'), labels.get(obj.status, obj.status))
    status_display.short_description = '진행 상태'

    def response_count(self, obj):
        return format_html('<b>{}</b>명 참여', obj.responses.count())
    response_count.short_description = '참여 현황'


# ════════════════════════════════════════════════════════════════════
# 🎖️ 회원 등급
# ════════════════════════════════════════════════════════════════════
@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    """회원 등급 기준을 설정합니다. 포인트·활동수 기준을 충족하면 자동 승급됩니다"""
    list_display   = ('name', 'order', 'required_points',
                       'required_activities', 'badge_color_display', 'is_active')
    list_editable  = ('required_points', 'required_activities', 'order')
    ordering       = ('order',)
    list_per_page  = 10

    def badge_color_display(self, obj):
        return format_html(
            '<span class="badge bg-{}" style="padding:4px 10px;">{}</span>',
            obj.badge_color, obj.get_badge_color_display()
        )
    badge_color_display.short_description = '등급 색상 미리보기'


# ════════════════════════════════════════════════════════════════════
# ⚙️ 사이트 설정
# ════════════════════════════════════════════════════════════════════
@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    """홈 화면 히어로 배경·색상 등 사이트 전체 설정을 관리합니다"""
    list_display  = ('site_name', 'hero_color', 'updated_at')
    fields        = ('site_name', 'hero_color', 'hero_image')
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = SiteConfig.objects.get_or_create(id=1)
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:core_siteconfig_change', args=[obj.pk])
        )


# ════════════════════════════════════════════════════════════════════
# 📋 관리자 행위 로그 (개인정보보호법 제29조)
# ════════════════════════════════════════════════════════════════════
@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    """관리자의 모든 민감 행위(비밀번호 초기화·등급변경·계정 활성화 등)가 자동 기록됩니다.
    개인정보보호법 제29조 안전조치 의무에 따라 수정·삭제가 제한됩니다"""
    list_display   = ('created_at', 'admin_display', 'action_display',
                       'target_display', 'detail', 'ip_address')
    list_filter    = ('action',)
    search_fields  = ('admin__nickname', 'admin__username',
                       'target_user__nickname', 'detail')
    ordering       = ('-created_at',)
    list_per_page  = 30
    readonly_fields = ('admin', 'target_user', 'action', 'detail',
                        'ip_address', 'created_at')

    def admin_display(self, obj):
        name = obj.admin.nickname or obj.admin.username if obj.admin else '(삭제된 계정)'
        return format_html('<span style="font-weight:600;color:#1a7a4a;">{}</span>', name)
    admin_display.short_description = '처리 관리자'

    def action_display(self, obj):
        colors = {
            'pw_reset':     '#f59e0b',
            'grade_change': '#3b82f6',
            'activate':     '#10b981',
            'deactivate':   '#ef4444',
            'verify':       '#8b5cf6',
            'reject':       '#6b7280',
        }
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colors.get(obj.action, '#9ca3af'), obj.get_action_display()
        )
    action_display.short_description = '행위 종류'

    def target_display(self, obj):
        if obj.target_user:
            return format_html('{} <span style="color:#9ca3af;font-size:0.85em;">({})</span>',
                obj.target_user.nickname or '-', obj.target_user.username)
        return '(삭제된 계정)'
    target_display.short_description = '대상 회원'

    def has_add_permission(self, request):
        return False  # 로그는 직접 생성 불가

    def has_change_permission(self, request, obj=None):
        return False  # 로그는 수정 불가

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # 최고관리자만 삭제 가능
