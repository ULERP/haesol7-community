from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
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

# ============================================================
# 사이트 제목 설정
# ============================================================
admin.site.site_header  = '🌿 해솔마을 7단지 지킴이 관리자'
admin.site.site_title   = '해솔7 관리자'
admin.site.index_title  = '관리 메뉴'


# ============================================================
# 👤 회원 관리
# ============================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display   = ('username', 'nickname', 'dong_ho', 'mileage_points', 'manners_score', 'is_verified', 'date_joined')
    list_filter    = ('is_verified', 'is_staff', 'is_active')
    search_fields  = ('username', 'nickname', 'dong', 'ho')
    ordering       = ('-date_joined',)
    list_per_page  = 30
    fieldsets = UserAdmin.fieldsets + (
        ('🏠 입주민 정보', {'fields': ('nickname', 'dong', 'ho', 'unit_number', 'bio', 'avatar')}),
        ('🏅 활동 정보',   {'fields': ('mileage_points', 'manners_score', 'is_verified', 'current_badges')}),
    )

    def dong_ho(self, obj):
        if obj.dong:
            return f"{obj.dong}동 {obj.ho}호"
        return "-"
    dong_ho.short_description = '동/호수'

    class Meta:
        verbose_name        = '입주민'
        verbose_name_plural = '입주민 목록'


# ============================================================
# 🏅 배지 관리
# ============================================================
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display   = ('title', 'category_display', 'required_points', 'required_activities', 'is_active', 'status_display')
    list_filter    = ('category', 'is_active')
    search_fields  = ('title', 'description')
    list_editable  = ('required_points', 'required_activities', 'is_active')
    list_per_page  = 20

    def category_display(self, obj):
        colors = {'security': 'primary', 'environment': 'success', 'community': 'info', 'helping': 'warning'}
        color  = colors.get(obj.category, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_category_display())
    category_display.short_description = '카테고리'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 활성</span>')
        return format_html('<span style="color:red;">● 비활성</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '배지'
        verbose_name_plural = '배지 목록'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display   = ('user', 'badge', 'earned_at', 'is_displayed')
    list_filter    = ('badge', 'is_displayed')
    search_fields  = ('user__nickname', 'user__username', 'badge__title')
    raw_id_fields  = ('user', 'badge')
    list_per_page  = 30

    class Meta:
        verbose_name        = '회원 보유 배지'
        verbose_name_plural = '회원 보유 배지 목록'


# ============================================================
# 🤝 봉사활동 관리
# ============================================================
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display   = ('name', 'activity_type', 'base_points', 'points_per_hour', 'is_active')
    list_filter    = ('activity_type', 'is_active')
    search_fields  = ('name', 'description')
    list_editable  = ('base_points', 'points_per_hour', 'is_active')
    list_per_page  = 20

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 운영중</span>')
        return format_html('<span style="color:gray;">● 중단</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '봉사활동 종류'
        verbose_name_plural = '봉사활동 종류 목록'


@admin.register(ActivityProof)
class ActivityProofAdmin(admin.ModelAdmin):
    list_display   = ('user', 'activity', 'status_display', 'status', 'points_earned', 'submitted_at')
    list_filter    = ('status', 'activity')
    search_fields  = ('user__nickname', 'user__username')
    list_editable  = ('status',)
    actions        = ['approve_selected', 'reject_selected']
    raw_id_fields  = ('user', 'activity')
    list_per_page  = 30
    readonly_fields = ('submitted_at',)

    def status_display(self, obj):
        colors = {'pending': 'orange', 'approved': 'green', 'rejected': 'red'}
        labels = {'pending': '⏳ 대기중', 'approved': '✅ 승인', 'rejected': '❌ 반려'}
        color  = colors.get(obj.status, 'gray')
        label  = labels.get(obj.status, obj.status)
        return format_html('<span style="color:{};">{}</span>', color, label)
    status_display.short_description = '승인 상태'

    def approve_selected(self, request, queryset):
        for proof in queryset.filter(status='pending'):
            proof.status = 'approved'
            proof.save()
        self.message_user(request, f"✅ {queryset.count()}개 활동을 승인했습니다.")
    approve_selected.short_description = "✅ 선택한 활동 승인"

    def reject_selected(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"❌ {queryset.count()}개 활동을 반려했습니다.")
    reject_selected.short_description = "❌ 선택한 활동 반려"

    class Meta:
        verbose_name        = '활동 인증 신청'
        verbose_name_plural = '활동 인증 신청 목록'


# ============================================================
# 📋 게시판 관리
# ============================================================
@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display   = ('name', 'board_type', 'order', 'is_active', 'status_display')
    list_editable  = ('order', 'is_active')
    search_fields  = ('name',)
    list_per_page  = 20

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개</span>')
        return format_html('<span style="color:gray;">● 숨김</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '게시판'
        verbose_name_plural = '게시판 목록'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display   = ('title', 'author', 'board', 'view_count', 'like_count', 'created_at', 'status_display')
    list_filter    = ('board', 'is_active')
    search_fields  = ('title', 'content', 'author__nickname')
    raw_id_fields  = ('author', 'board')
    list_per_page  = 30
    readonly_fields = ('created_at', 'view_count')

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = '좋아요'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개</span>')
        return format_html('<span style="color:red;">● 삭제됨</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '게시글'
        verbose_name_plural = '게시글 목록'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
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
        return format_html('<span style="color:red;">● 삭제됨</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '댓글'
        verbose_name_plural = '댓글 목록'


# ============================================================
# 📂 관리 문서
# ============================================================
@admin.register(ManagementDocument)
class ManagementDocumentAdmin(admin.ModelAdmin):
    list_display   = ('title', 'category', 'author', 'view_count', 'has_file', 'is_active', 'created_at')
    list_filter    = ('category', 'is_active')
    search_fields  = ('title', 'content')
    list_editable  = ('is_active',)
    raw_id_fields  = ('author',)
    list_per_page  = 20
    readonly_fields = ('created_at', 'updated_at', 'view_count')

    def has_file(self, obj):
        if obj.file:
            return format_html('<span style="color:green;">📎 있음</span>')
        return format_html('<span style="color:gray;">-</span>')
    has_file.short_description = '첨부파일'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 공개</span>')
        return format_html('<span style="color:gray;">● 숨김</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '관리 문서'
        verbose_name_plural = '관리 문서 목록'


# ============================================================
# ❤️ 이웃 온기 점수
# ============================================================
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display   = ('rater', 'rated_user', 'score_display', 'short_comment', 'created_at')
    list_filter    = ('score',)
    search_fields  = ('rater__nickname', 'rated_user__nickname', 'comment')
    raw_id_fields  = ('rater', 'rated_user')
    list_per_page  = 30
    readonly_fields = ('created_at',)

    def score_display(self, obj):
        stars = '⭐' * obj.score
        return format_html('{}  ({}점)', stars, obj.score)
    score_display.short_description = '평점'

    def short_comment(self, obj):
        if obj.comment:
            return obj.comment[:30] + '...' if len(obj.comment) > 30 else obj.comment
        return '-'
    short_comment.short_description = '한마디'

    class Meta:
        verbose_name        = '이웃 온기 평가'
        verbose_name_plural = '이웃 온기 평가 목록'


# ============================================================
# 👥 소모임 관리
# ============================================================
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display   = ('name', 'group_type', 'creator', 'member_count', 'status_display', 'created_at')
    list_filter    = ('group_type', 'is_active')
    search_fields  = ('name', 'description', 'creator__nickname')
    raw_id_fields  = ('creator',)
    list_per_page  = 20

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '회원 수'

    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">● 운영중</span>')
        return format_html('<span style="color:gray;">● 해산</span>')
    status_display.short_description = '상태'

    class Meta:
        verbose_name        = '소모임'
        verbose_name_plural = '소모임 목록'


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display   = ('user', 'group', 'role_display', 'joined_at')
    list_filter    = ('role',)
    search_fields  = ('user__nickname', 'group__name')
    raw_id_fields  = ('user', 'group')
    list_per_page  = 30

    def role_display(self, obj):
        if obj.role == 'leader':
            return format_html('<span style="color:#e67e22;">👑 모임장</span>')
        return format_html('<span style="color:#27ae60;">회원</span>')
    role_display.short_description = '역할'

    class Meta:
        verbose_name        = '소모임 회원'
        verbose_name_plural = '소모임 회원 목록'


# ============================================================
# 📅 봉사 일정
# ============================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display   = ('post', 'start_time', 'end_time', 'location', 'created_at')
    list_filter    = ('start_time',)
    search_fields  = ('post__title', 'location')
    list_per_page  = 20
    readonly_fields = ('created_at',)

    class Meta:
        verbose_name        = '봉사 일정'
        verbose_name_plural = '봉사 일정 목록'


# ============================================================
# 🔔 알림
# ============================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display   = ('recipient', 'title', 'type_display', 'read_display', 'created_at')
    list_filter    = ('notification_type', 'is_read')
    search_fields  = ('recipient__nickname', 'title', 'message')
    raw_id_fields  = ('recipient',)
    list_per_page  = 30
    readonly_fields = ('created_at',)

    def type_display(self, obj):
        icons = {'activity': '🤝', 'announcement': '📢', 'badge': '🏅', 'community': '👥', 'event': '📅'}
        icon  = icons.get(obj.notification_type, '🔔')
        return format_html('{} {}', icon, obj.get_notification_type_display())
    type_display.short_description = '알림 종류'

    def read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color:gray;">읽음</span>')
        return format_html('<span style="color:blue;font-weight:bold;">● 안읽음</span>')
    read_display.short_description = '읽음 여부'

    class Meta:
        verbose_name        = '알림'
        verbose_name_plural = '알림 목록'


# ============================================================
# 📊 설문조사
# ============================================================
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display   = ('title', 'creator', 'status_display', 'survey_type', 'response_count', 'created_at')
    list_filter    = ('status', 'survey_type')
    search_fields  = ('title', 'creator__nickname')
    raw_id_fields  = ('creator',)
    list_per_page  = 20
    readonly_fields = ('created_at',)

    def status_display(self, obj):
        colors = {'draft': 'gray', 'active': 'green', 'closed': 'red'}
        labels = {'draft': '✏️ 작성중', 'active': '✅ 진행중', 'closed': '🔒 마감'}
        color  = colors.get(obj.status, 'gray')
        label  = labels.get(obj.status, obj.status)
        return format_html('<span style="color:{};">{}</span>', color, label)
    status_display.short_description = '상태'

    def response_count(self, obj):
        return obj.responses.count()
    response_count.short_description = '응답 수'

    class Meta:
        verbose_name        = '설문조사'
        verbose_name_plural = '설문조사 목록'


# ============================================================
# 🎖️ 회원 등급
# ============================================================
@admin.register(MemberGrade)
class MemberGradeAdmin(admin.ModelAdmin):
    list_display   = ('name', 'order', 'required_points', 'required_activities', 'badge_color_display')
    list_editable  = ('required_points', 'required_activities')
    ordering       = ('order',)
    list_per_page  = 10

    def badge_color_display(self, obj):
        return format_html(
            '<span class="badge bg-{}" style="padding:4px 10px;">{}</span>',
            obj.badge_color, obj.get_badge_color_display()
        )
    badge_color_display.short_description = '등급 색상'

    class Meta:
        verbose_name        = '회원 등급'
        verbose_name_plural = '회원 등급 목록'

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display  = ['title', 'event_type', 'start_time', 'creator', 'visibility', 'is_approved']
    list_filter   = ['event_type', 'visibility', 'is_approved']
    search_fields = ['title', 'creator__username']
    actions       = ['approve_events']

    def approve_events(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_approved=True, visibility='public', approved_by=request.user, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}개 일정이 승인되었습니다.')
    approve_events.short_description = '선택 일정 승인'


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'hero_color', 'updated_at']

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()
