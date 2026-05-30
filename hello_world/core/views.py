from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from rest_framework import viewsets
from rest_framework.response import Response
from .models import (
    Activity, ActivityProof, Post, Group, Meetup,
    Board, Comment, PostLike, CustomUser,
    MemberGrade, BoardGradePermission
)
from .serializers import PostSerializer, GroupSerializer, MeetupSerializer


# ============================================================================
# 권한 헬퍼
# ============================================================================
def get_user_grade(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return MemberGrade.objects.order_by('-order').first()
    grade_names = user.groups.values_list('name', flat=True)
    return MemberGrade.objects.filter(
        name__in=grade_names, is_active=True
    ).order_by('-order').first()

def check_board_permission(user, board, action='read'):
    if user.is_superuser:
        return True
    if not user.is_authenticated:
        return False
    user_grade = get_user_grade(user)
    if not user_grade:
        return False
    perm = BoardGradePermission.objects.filter(board=board, grade=user_grade).first()
    if perm:
        if action == 'read':    return perm.can_read
        if action == 'write':   return perm.can_write
        if action == 'comment': return perm.can_comment
    if action == 'read':    return user_grade.can_read_all
    if action == 'write':   return user_grade.can_write
    if action == 'comment': return user_grade.can_comment
    return False


# ============================================================================
# 메인
# ============================================================================
def index(request):
    from .models import ManagementDocument, Post, Board
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # 공지 게시판 글
    try:
        notice_board = Board.objects.filter(board_type='notice', is_active=True).first()
        notice_posts = Post.objects.filter(board=notice_board, is_active=True).order_by('-created_at')[:3] if notice_board else []
    except: notice_posts = []
    # 관리 문서
    try: recent_docs = ManagementDocument.objects.filter(is_active=True).order_by('-updated_at')[:3]
    except: recent_docs = []
    # 전체 입주민
    try: all_users = User.objects.filter(is_active=True).exclude(id=request.user.id if request.user.is_authenticated else 0).order_by('username')[:30]
    except: all_users = []
    # 온라인 입주민 (최근 5분 이내 - 간단히 최근 가입자로 대체)
    try: online_users = User.objects.filter(is_active=True).order_by('-last_login')[:8]
    except: online_users = []
    # 내 소모임
    try:
        from .models import Group
        my_groups = Group.objects.filter(members=request.user, is_active=True)[:5] if request.user.is_authenticated else []
    except: my_groups = []

    boards = Board.objects.filter(is_active=True).order_by('order')
    recent_posts = Post.objects.filter(is_active=True).order_by('-created_at')[:10]
    upcoming_events = Activity.objects.filter(is_active=True).order_by('created_at')[:5]
    from .models import Badge, ActivityProof, Meetup
    activities_count = Activity.objects.filter(is_active=True).count()
    approved_activities_count = ActivityProof.objects.filter(status='approved').count()
    badges_count = Badge.objects.filter(is_active=True).count()
    upcoming_meetups = Meetup.objects.filter(status='recruiting').order_by('scheduled_at')[:3]
    groups_count = Group.objects.filter(is_active=True).count()
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from .models import PostLike, Survey, Poll, PublicChat, Notice, Event

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    # 인기 게시글 (최근 7일, 좋아요 많은 순)
    hot_posts = Post.objects.filter(
        is_active=True, created_at__gte=week_ago
    ).order_by('-like_count', '-created_at')[:5]

    # 진행중인 설문 (status: draft/active/closed)
    try:
        active_surveys = Survey.objects.filter(
            status='active'
        ).annotate(resp_count=Count('responses')).order_by('-resp_count')[:3]
    except: active_surveys = []

    # 진행중인 채팅 투표
    try:
        active_polls = Poll.objects.filter(
            is_active=True
        ).order_by('-created_at')[:3]
    except: active_polls = []

    # 최근 공지
    try:
        recent_notices = Notice.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=now)
        ).order_by('-is_pinned', '-created_at')[:3]
    except: recent_notices = []

    # 최근 채팅 (미리보기용)
    try:
        recent_chats = PublicChat.objects.filter(
            is_active=True
        ).select_related('author').order_by('-created_at')[:5]
    except: recent_chats = []

    # 봉사 일정
    try:
        upcoming_volunteer = Event.objects.filter(
            start_time__gte=now
        ).order_by('start_time')[:3]
    except: upcoming_volunteer = []

    # 단지 현황 숫자
    from django.contrib.auth import get_user_model
    User2 = get_user_model()
    total_users    = User2.objects.filter(is_active=True).count()
    verified_users = User2.objects.filter(is_active=True, is_verified=True).count()

    return render(request, 'index.html', {
        'boards': boards,
        'recent_posts': recent_posts,
        'hot_posts': hot_posts,
        'upcoming_events': upcoming_events,
        'notice_posts': notice_posts,
        'recent_docs': recent_docs,
        'all_users': all_users,
        'online_users': online_users,
        'my_groups': my_groups,
        'activities_count': activities_count,
        'approved_activities_count': approved_activities_count,
        'badges_count': badges_count,
        'upcoming_meetups': upcoming_meetups,
        'groups_count': groups_count,
        'active_surveys': active_surveys,
        'active_polls': active_polls,
        'recent_notices': recent_notices,
        'recent_chats': recent_chats,
        'upcoming_volunteer': upcoming_volunteer,
        'total_users': total_users,
        'verified_users': verified_users,
    })


# ============================================================================
# 회원
# ============================================================================
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active or user.is_superuser:
                auth_login(request, user)
                return redirect('index')
            else:
                messages.error(request, '관리자 승인 대기 중입니다.')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    return render(request, 'registration/login.html')

def signup(request):
    if request.method == 'POST':
        username  = request.POST.get('username')
        real_name = request.POST.get('real_name')
        dong      = request.POST.get('dong')
        ho        = request.POST.get('ho')
        phone     = request.POST.get('phone', '')
        email     = request.POST.get('email', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'registration/signup.html')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, '이미 사용 중인 아이디입니다.')
            return render(request, 'registration/signup.html')
        user = CustomUser.objects.create_user(
            username=username,
            password=password1,
            unit_number=f'{dong}동 {ho}호',
            phone_number=phone,
            email=email,
            first_name=real_name,
        )
        messages.success(request, '가입 완료! 로그인해주세요.')
        return redirect('login')
    return render(request, 'registration/signup.html')

@login_required
def mypage(request):
    user = request.user
    from .models import Group, GroupMember, UserBadge, Survey, SurveyResponse, Rating
    my_posts       = Post.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    my_comments    = Comment.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    my_activities  = ActivityProof.objects.filter(user=user).order_by('-submitted_at')[:5]
    my_badges      = UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')
    my_groups      = Group.objects.filter(members=user, is_active=True)
    my_surveys     = Survey.objects.filter(creator=user).order_by('-created_at')[:3]
    my_responses   = SurveyResponse.objects.filter(respondent=user).select_related('survey').order_by('-submitted_at')[:3]
    received_ratings = Rating.objects.filter(rated_user=user).order_by('-created_at')[:5]
    total_activities = ActivityProof.objects.filter(user=user, status='approved').count()
    pending_activities = ActivityProof.objects.filter(user=user, status='pending').count()
    user_grade_name = get_user_grade(user)
    try:
        user_grade = MemberGrade.objects.get(name=str(user_grade_name)) if user_grade_name else None
    except:
        user_grade = None
    from .models import Letter, Complaint, Notification
    from django.utils import timezone
    from datetime import timedelta
    unread_letters   = Letter.objects.filter(receiver=user, is_read=False, receiver_deleted=False).count()
    my_complaints    = Complaint.objects.filter(author=user).order_by('-created_at')[:3]
    pending_complaints = Complaint.objects.filter(author=user, status__in=['received','reviewing']).count()
    unread_noti      = Notification.objects.filter(user=user, is_read=False).count()
    week_ago         = timezone.now() - timedelta(days=7)
    recent_posts     = Post.objects.filter(author=user, created_at__gte=week_ago).count()

    return render(request, 'mypage.html', {
        'user': user,
        'my_posts': my_posts,
        'my_comments': my_comments,
        'my_activities': my_activities,
        'my_badges': my_badges,
        'my_groups': my_groups,
        'my_surveys': my_surveys,
        'my_responses': my_responses,
        'received_ratings': received_ratings,
        'user_grade': user_grade,
        'total_activities': total_activities,
        'pending_activities': pending_activities,
        'total_points': user.mileage_points,
        'unread_letters': unread_letters,
        'my_complaints': my_complaints,
        'pending_complaints': pending_complaints,
        'unread_noti': unread_noti,
        'recent_posts': recent_posts,
    })


# ============================================================================
# 게시판
# ============================================================================
def board_list(request):
    boards = Board.objects.filter(is_active=True).order_by('order')
    return render(request, 'board_list.html', {'boards': boards})

def board_detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    if not check_board_permission(request.user, board, 'read'):
        return HttpResponseForbidden('이 게시판을 열람할 권한이 없습니다.')
    tag   = request.GET.get('tag', '')
    posts = Post.objects.filter(board=board, is_active=True)
    if tag:
        posts = posts.filter(tag=tag)
    return render(request, 'board_detail.html', {
        'board': board,
        'posts': posts,
        'tags': board.get_tags_list(),
        'selected_tag': tag,
        'can_write': check_board_permission(request.user, board, 'write'),
        'can_comment': check_board_permission(request.user, board, 'comment'),
    })

def post_list(request):
    board_id = request.GET.get('board_id')
    selected_board = None
    selected_tag   = request.GET.get('tag', '')
    posts = Post.objects.filter(is_active=True)
    if board_id:
        selected_board = get_object_or_404(Board, pk=board_id, is_active=True)
        posts = posts.filter(board=selected_board)
    if selected_tag:
        posts = posts.filter(tag=selected_tag)
    boards = Board.objects.filter(is_active=True).order_by('order')
    return render(request, 'core/post_list.html', {
        'posts': posts.order_by('-created_at'),
        'boards': boards,
        'selected_board': selected_board,
        'selected_tag': selected_tag,
    })

def post_detail(request, pk):
    post     = get_object_or_404(Post, pk=pk, is_active=True)
    Post.objects.filter(pk=pk).update(view_count=post.view_count+1)
    comments = post.comments.filter(is_active=True, parent=None)
    user_groups = []
    if request.user.is_authenticated:
        from .models import Group
        user_groups = Group.objects.filter(members=request.user, is_active=True)[:5]
    # 연결된 설문
    linked_surveys = Survey.objects.filter(source_post=post, status__in=['active','closed'])
    # 관련 게시글
    related_posts = post.related_posts.filter(is_active=True)[:5]
    return render(request, 'post_detail.html', {'user_groups': user_groups,
        'post': post,
        'comments': comments,
        'can_comment': check_board_permission(request.user, post.board, 'comment'),
        'can_write':   check_board_permission(request.user, post.board, 'write'),
        'linked_surveys': linked_surveys,
        'related_posts': related_posts,
    })

@login_required
def post_write(request, board_id):
    from .forms import PostForm, TradeForm, EventForm
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    if not check_board_permission(request.user, board, 'write'):
        return HttpResponseForbidden('이 게시판에 글을 쓸 권한이 없습니다.')
    extra_form_class = TradeForm if board.board_type == 'trade' else (EventForm if board.board_type == 'event' else None)
    if request.method == 'POST':
        post_form  = PostForm(request.POST, board=board)
        extra_form = extra_form_class(request.POST) if extra_form_class else None
        if post_form.is_valid() and (extra_form is None or extra_form.is_valid()):
            post = post_form.save(commit=False)
            post.board  = board
            post.author = request.user
            post.save()
            if extra_form:
                extra = extra_form.save(commit=False)
                extra.post = post
                extra.save()
            # 이미지 첨부 처리
            images = request.FILES.getlist('images')
            from .models import PostImage
            for i, image in enumerate(images):
                PostImage.objects.create(post=post, image=image, order=i)
            return redirect('post_detail', pk=post.pk)
    else:
        post_form  = PostForm(board=board)
        extra_form = extra_form_class() if extra_form_class else None
    return render(request, 'post_write.html', {
        'board': board,
        'post_form': post_form,
        'extra_form': extra_form,
        'my_surveys': Survey.objects.filter(creator=request.user, status='active') if request.user.is_authenticated else [],
    })

@login_required
def board_post_create(request):
    from .forms import PostForm
    boards = Board.objects.filter(is_active=True).order_by('order')
    board_id = request.GET.get('board_id') or request.POST.get('board_id')
    board = get_object_or_404(Board, pk=board_id) if board_id else None
    if request.method == 'POST' and board:
        form = PostForm(request.POST, board=board)
        if form.is_valid():
            post = form.save(commit=False)
            post.board  = board
            post.author = request.user
            # 설문 삽입 처리
            survey_id = request.POST.get('linked_survey_id')
            if survey_id:
                try:
                    from .models import Survey
                    survey = Survey.objects.get(pk=int(survey_id), creator=request.user)
                    post.linked_survey = survey
                    # 설문의 source_post 연결
                    if not survey.source_post:
                        survey.source_post = post
                        survey.save()
                except: pass
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(board=board)
    return render(request, 'post_form.html', {'form': form, 'boards': boards, 'selected_board': board})

@login_required
def post_create(request):
    return board_post_create(request)

@login_required
def post_edit(request, pk):
    from .forms import PostForm
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('수정 권한이 없습니다.')
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post, board=post.board)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post, board=post.board)
    return render(request, 'post_edit.html', {'board': post.board, 'post': post, 'post_form': form})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden('삭제 권한이 없습니다.')
    if request.method == 'POST':
        post.is_active = False
        post.save()
        return redirect('board_detail', board_id=post.board.id)
    return render(request, 'post_delete_confirm.html', {'post': post})

@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        Post.objects.filter(pk=post_id).update(like_count=post.like_count-1)
        liked = False
    else:
        Post.objects.filter(pk=post_id).update(like_count=post.like_count+1)
        liked = True
    return JsonResponse({'liked': liked, 'count': Post.objects.get(pk=post_id).like_count})

@login_required
def comment_create(request, post_id):
    if request.method == 'POST':
        post    = get_object_or_404(Post, pk=post_id)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        if content:
            Comment.objects.create(
                post=post, author=request.user,
                content=content,
                parent_id=parent_id if parent_id else None,
            )
    return redirect('post_detail', pk=post_id)


# ============================================================================
# 활동 인증
# ============================================================================
@login_required
def activity_proof_submit(request):
    from .forms import ActivityProofForm
    if request.method == 'POST':
        form = ActivityProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.user   = request.user
            proof.status = 'pending'
            proof.save()
            messages.success(request, '활동 인증이 제출됐습니다! 관리자 승인 후 포인트가 지급됩니다.')
            return redirect('activity_proof_list')
    else:
        form = ActivityProofForm()
    return render(request, 'activity_proof_submit.html', {'form': form})

@login_required
def activity_proof_list(request):
    proofs = ActivityProof.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'activity_proof_list.html', {'proofs': proofs})

def activity_list(request):
    activities = Activity.objects.filter(is_active=True)
    return render(request, 'core/activity_list.html', {'activities': activities})


# ============================================================================
# API ViewSets
# ============================================================================
class PostViewSet(viewsets.ModelViewSet):
    queryset         = Post.objects.all()
    serializer_class = PostSerializer
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class GroupViewSet(viewsets.ModelViewSet):
    queryset         = Group.objects.all()
    serializer_class = GroupSerializer

class MeetupViewSet(viewsets.ModelViewSet):
    queryset         = Meetup.objects.all()
    serializer_class = MeetupSerializer


# ============================================================================
# 프로필 수정
# ============================================================================
@login_required

@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        user.nickname     = request.POST.get('nickname', '')
        user.first_name   = request.POST.get('first_name', '')
        dong = request.POST.get('dong', '').strip()
        ho   = request.POST.get('ho', '').strip()
        user.dong = dong
        user.ho   = ho
        user.unit_number = f"{dong}동 {ho}호".strip() if dong or ho else ''
        user.phone_number = request.POST.get('phone_number', '')
        user.introduction = request.POST.get('introduction', '')
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, '프로필이 수정됐습니다.')
        return redirect('mypage')
    return render(request, 'profile_edit.html', {'user': user})


# ============================================================================
# 봉사활동 달력
# ============================================================================
def volunteer_calendar(request):
    from .models import Meetup
    meetups = Meetup.objects.filter(
        status__in=['recruiting', 'confirmed']
    ).values('id', 'title', 'scheduled_at', 'location', 'status', 'max_participants')
    
    import json
    from django.utils import timezone
    
    events = []
    for m in meetups:
        events.append({
            'id': m['id'],
            'title': m['title'],
            'start': m['scheduled_at'].isoformat() if m['scheduled_at'] else '',
            'location': m['location'],
            'status': m['status'],
            'url': f'/volunteer/{m["id"]}/',
        })
    
    return render(request, 'volunteer_calendar.html', {
        'events_json': json.dumps(events, ensure_ascii=False),
    })

def volunteer_detail(request, pk):
    from .models import Meetup
    meetup = get_object_or_404(Meetup, pk=pk)
    is_joined = False
    if request.user.is_authenticated:
        is_joined = meetup.participants.filter(pk=request.user.pk).exists()
    return render(request, 'volunteer_detail.html', {
        'meetup': meetup,
        'is_joined': is_joined,
        'participant_count': meetup.participants.count(),
    })

@login_required
def volunteer_join(request, pk):
    from .models import Meetup
    meetup = get_object_or_404(Meetup, pk=pk)
    if request.method == 'POST':
        if meetup.participants.filter(pk=request.user.pk).exists():
            meetup.participants.remove(request.user)
            messages.info(request, '참가 신청이 취소됐습니다.')
        else:
            if meetup.max_participants and meetup.participants.count() >= meetup.max_participants:
                messages.error(request, '참가 인원이 마감됐습니다.')
            else:
                meetup.participants.add(request.user)
                messages.success(request, '참가 신청이 완료됐습니다!')
    return redirect('volunteer_detail', pk=pk)


# ============================================================================
# 검색
# ============================================================================
def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Post.objects.filter(
            is_active=True
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(tag__icontains=query)
        ).order_by('-created_at')
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'count': len(results) if results else 0,
    })


# ============================================================================
# 검색
# ============================================================================
from django.db.models import Q

def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Post.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tag__icontains=query)
        ).order_by('-created_at')
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'count': results.count() if query else 0,
    })


# ============================================================================
# 검색
# ============================================================================
from django.db.models import Q

def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = Post.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tag__icontains=query)
        ).order_by('-created_at')
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'count': results.count() if query else 0,
    })


# ============================================================================
# 알림 시스템
# ============================================================================
@login_required
def notification_list(request):
    from .models import Notification
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    # 읽음 처리
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notification_list.html', {
        'notifications': notifications,
    })

def notification_count(request):
    from .models import Notification
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
    else:
        count = 0
    return JsonResponse({'count': count})


# ============================================================================
# 알림 시스템
# ============================================================================
@login_required
def notification_list(request):
    from .models import Notification
    notis = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return render(request, 'notification_list.html', {'notifications': notis})

def notification_count(request):
    from .models import Notification
    count = 0
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
    return JsonResponse({'count': count})


# ============================================================================
# RAG 챗봇 (관리 규약 안내)
# ============================================================================
@login_required
def chatbot(request):
    from .models import ChatHistory, ManagementDocument
    chat_history = ChatHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    return render(request, 'chatbot.html', {'chat_history': chat_history})

@login_required
def chatbot_ask(request):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)
    
    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    
    if not question:
        return JsonResponse({'error': '질문을 입력하세요'}, status=400)

    from .models import ChatHistory, ManagementDocument
    
    # 관련 문서 검색
    docs = ManagementDocument.objects.filter(
        is_active=True
    ).filter(
        Q(title__icontains=question) |
        Q(content__icontains=question) |
        Q(category__icontains=question)
    )[:3]
    
    doc_context = ''
    referenced = []
    for doc in docs:
        doc_context += f'\n[{doc.category}] {doc.title}:\n{doc.content[:500]}\n'
        referenced.append({'title': doc.title, 'category': doc.category})
    
    # Claude API 호출
    import requests as req
    
    system_prompt = f'''당신은 해솔마을7단지 아파트 관리 안내 도우미입니다.
주민들의 질문에 친근하고 따뜻한 말투로 답변해주세요.
아래 관리 규약 문서를 참고하여 답변하세요.

{doc_context if doc_context else '관련 문서가 없습니다. 일반적인 아파트 생활 상식으로 답변해주세요.'}'''

    try:
        response = req.post(
            'https://api.anthropic.com/v1/messages',
            headers={'Content-Type': 'application/json'},
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 1000,
                'system': system_prompt,
                'messages': [{'role': 'user', 'content': question}]
            },
            timeout=30
        )
        result = response.json()
        answer = result['content'][0]['text']
        confidence = 0.9 if docs else 0.5
    except Exception as e:
        answer = '죄송합니다. 현재 답변을 생성할 수 없습니다. 관리사무소에 문의해주세요.'
        confidence = 0.0
        referenced = []

    # 대화 기록 저장
    ChatHistory.objects.create(
        user=request.user,
        question=question,
        answer=answer,
        referenced_documents=referenced,
        confidence_score=confidence,
    )

    return JsonResponse({
        'answer': answer,
        'referenced': referenced,
        'confidence': confidence,
    })


# ============================================================================
# 관리 문서 게시판
# ============================================================================
def management_docs(request):
    from .models import ManagementDocument
    category = request.GET.get('category', '')
    query = request.GET.get('q', '')
    docs = ManagementDocument.objects.filter(is_active=True)
    if category:
        docs = docs.filter(category=category)
    if query:
        docs = docs.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )
    categories = ManagementDocument.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct()
    return render(request, 'management_docs.html', {
        'docs': docs.order_by('category', 'title'),
        'categories': categories,
        'selected_category': category,
        'query': query,
    })

def management_doc_detail(request, pk):
    from .models import ManagementDocument
    doc = get_object_or_404(ManagementDocument, pk=pk, is_active=True)
    return render(request, 'management_doc_detail.html', {'doc': doc})


# =====================================================
# 채팅 시스템
# =====================================================
from .models import DirectMessage, PublicChat, GroupChat, Group, CustomUser

def public_chat(request):
    from .models import PublicChat, Group
    from django.contrib.auth import get_user_model
    User = get_user_model()
    recent_chats = PublicChat.objects.filter(is_active=True).select_related('author').order_by('-created_at')[:50]
    my_groups = Group.objects.filter(members=request.user, is_active=True)[:10] if request.user.is_authenticated else []
    online_users = User.objects.filter(is_active=True).order_by('-last_login')[:20]
    all_users = User.objects.filter(is_active=True).order_by('nickname')[:50]
    return render(request, 'chat/public_chat.html', {
        'recent_chats': list(reversed(recent_chats)),
        'my_groups': my_groups,
        'online_users': online_users,
        'all_users': all_users,
    })

def public_chat_messages(request):
    import json
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        chat = PublicChat.objects.create(author=request.user, message=msg)
        if image:
            chat.image = image
            chat.save()
        return JsonResponse({'status': 'ok', 'id': chat.id})

    since_id = int(request.GET.get('since', 0))
    # 고정 메시지
    pinned = PublicChat.objects.filter(is_pinned=True, is_active=True).select_related('author').order_by('-created_at')[:3]
    # 일반 메시지
    msgs = PublicChat.objects.filter(id__gt=since_id, is_active=True).select_related('author').order_by('created_at')[:60]

    def serialize(m):
        return {
            'id': m.id,
            'author': m.author.username,
            'unit': m.author.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.author == request.user,
            'is_pinned': m.is_pinned,
            'can_pin': request.user.is_staff,
        }

    return JsonResponse({
        'messages': [serialize(m) for m in msgs],
        'pinned': [serialize(m) for m in pinned] if since_id == 0 else [],
    })

def dm_list(request):
    """1:1 채팅 상대 목록 + 온라인 유저 + 전체 유저 검색"""
    if not request.user.is_authenticated:
        return redirect('login')
    from django.db.models import Q, Max
    from django.utils import timezone
    from datetime import timedelta

    # 기존 대화 상대
    partners_sent = DirectMessage.objects.filter(sender=request.user).values_list('receiver', flat=True).distinct()
    partners_recv = DirectMessage.objects.filter(receiver=request.user).values_list('sender', flat=True).distinct()
    partner_ids = set(list(partners_sent) + list(partners_recv))
    partners = CustomUser.objects.filter(id__in=partner_ids).exclude(id=request.user.id)

    # 온라인 유저 (최근 5분 이내 로그인)
    online_threshold = timezone.now() - timedelta(minutes=30)
    online_users = CustomUser.objects.filter(
        is_active=True,
        last_login__gte=online_threshold
    ).exclude(id=request.user.id).order_by('-last_login')[:20]

    # 전체 유저 (검색용)
    q = request.GET.get('q', '').strip()
    all_users = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id)
    if q:
        all_users = all_users.filter(
            Q(nickname__icontains=q) | Q(username__icontains=q) | Q(dong__icontains=q)
        )
    all_users = all_users.order_by('nickname')[:30]

    unread_count = DirectMessage.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'chat/dm_list.html', {
        'partners': partners,
        'online_users': online_users,
        'all_users': all_users,
        'unread_count': unread_count,
        'q': q,
    })

def direct_message(request, user_id):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')
    partner = get_object_or_404(CustomUser, pk=user_id)
    DirectMessage.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    all_users = CustomUser.objects.filter(is_active=True).exclude(id=request.user.id).order_by('username')[:20]
    return render(request, 'chat/direct_message.html', {'partner': partner, 'all_users': all_users})

def dm_messages(request, user_id):
    import json
    from django.http import JsonResponse
    from django.db.models import Q
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    partner = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            msg = data.get('message', '').strip()
        except Exception:
            msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        dm = DirectMessage.objects.create(sender=request.user, receiver=partner, message=msg)
        if image:
            dm.image = image
            dm.save()
        return JsonResponse({'status': 'ok', 'id': dm.id})

        Q(sender=request.user, receiver=partner) | Q(sender=partner, receiver=request.user),
        id__gt=since_id, is_active=True
    ).select_related('sender').order_by('created_at')[:100]
    # 읽음 처리
    DirectMessage.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'messages': [
        {
            'id': m.id,
            'author': m.sender.username,
            'unit': m.sender.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.sender == request.user,
            'is_read': m.is_read,
        } for m in msgs
    ]})

def group_chat(request, group_id):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')
    group = get_object_or_404(Group, pk=group_id)
    from .models import GroupMember
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    my_groups = Group.objects.filter(members=request.user, is_active=True)[:5]
    return render(request, 'chat/group_chat.html', {'group': group, 'members': members, 'my_groups': my_groups})

def group_chat_messages(request, group_id):
    import json
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    group = get_object_or_404(Group, pk=group_id)

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        if not msg and not image:
            return JsonResponse({'error': '내용 없음'}, status=400)
        chat = GroupChat.objects.create(group=group, sender=request.user, message=msg)
        if image:
            chat.image = image
            chat.save()
        return JsonResponse({'status': 'ok', 'id': chat.id})

    since_id = int(request.GET.get('since', 0))
    pinned = GroupChat.objects.filter(group=group, is_pinned=True, is_active=True).select_related('sender').order_by('-created_at')[:3]
    msgs = GroupChat.objects.filter(group=group, id__gt=since_id, is_active=True).select_related('sender').order_by('created_at')[:100]

    def serialize(m):
        return {
            'id': m.id,
            'author': m.sender.username,
            'unit': m.sender.unit_number,
            'message': m.message,
            'image': request.build_absolute_uri(m.image.url) if m.image else None,
            'time': m.created_at.strftime('%H:%M'),
            'is_me': m.sender == request.user,
            'is_pinned': m.is_pinned,
            'can_pin': request.user.is_staff,
        }

    return JsonResponse({
        'messages': [serialize(m) for m in msgs],
        'pinned': [serialize(m) for m in pinned] if since_id == 0 else [],
    })


# ============================================================================
# 소모임 (Group)
# ============================================================================
@login_required
def group_list(request):
    from .models import Group, GroupMember
    GROUP_TYPE_LABELS = {
        'hobby': '취미 활동', 'pet': '반려동물', 'sports': '스포츠',
        'volunteer': '자원봉사', 'learning': '학습', 'event': '정기 행사',
    }
    q          = request.GET.get('q', '').strip()
    gtype      = request.GET.get('type', '')
    order      = request.GET.get('order', 'newest')

    from django.db.models import Q, Count
    qs = Group.objects.filter(is_active=True, is_public=True)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if gtype:
        qs = qs.filter(group_type=gtype)
    if order == 'members':
        qs = qs.annotate(mc=Count('members')).order_by('-mc')
    else:
        qs = qs.order_by('-created_at')

    my_groups  = Group.objects.filter(members=request.user, is_active=True) if request.user.is_authenticated else Group.objects.none()
    all_groups = qs.exclude(members=request.user) if request.user.is_authenticated else qs

    return render(request, 'group_list.html', {
        'my_groups':         my_groups,
        'all_groups':        all_groups,
        'q':                 q,
        'gtype':             gtype,
        'order':             order,
        'group_type_labels': GROUP_TYPE_LABELS,
    })


@login_required
def group_create(request):
    from .models import Group, GroupMember
    GROUP_TYPE = [
        ('hobby', '취미 활동'), ('pet', '반려동물'), ('sports', '스포츠'),
        ('volunteer', '자원봉사'), ('learning', '학습'), ('event', '정기 행사'),
    ]
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        group_type = request.POST.get('group_type', 'hobby')
        location = request.POST.get('location', '').strip()
        regular_schedule = request.POST.get('regular_schedule', '').strip()
        member_limit = request.POST.get('member_limit') or None
        is_public = request.POST.get('is_public') == 'on'
        if not name:
            messages.error(request, '소모임 이름을 입력해주세요.')
            return render(request, 'group_form.html', {'group_types': GROUP_TYPE})
        group = Group.objects.create(
            name=name, description=description, group_type=group_type,
            creator=request.user, location=location,
            regular_schedule=regular_schedule,
            member_limit=int(member_limit) if member_limit else None,
            is_public=is_public,
        )
        GroupMember.objects.create(group=group, user=request.user, role='leader')
        messages.success(request, f'소모임 "{name}"이 만들어졌어요! 이웃을 초대해보세요.')
        return redirect('group_detail', pk=group.pk)
    return render(request, 'group_form.html', {'group_types': GROUP_TYPE})


def group_detail(request, pk):
    from .models import Group, GroupMember, GroupPost, GroupChat
    group = get_object_or_404(Group, pk=pk)
    is_member = False
    my_role = None
    if request.user.is_authenticated:
        membership = GroupMember.objects.filter(group=group, user=request.user, is_active=True).first()
        is_member = bool(membership)
        my_role = membership.role if membership else None
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    recent_posts = GroupPost.objects.filter(group=group).order_by('-created_at')[:5]
    return render(request, 'group_detail.html', {
        'group': group,
        'is_member': is_member,
        'my_role': my_role,
        'members': members,
        'recent_posts': recent_posts,
        'member_count': members.count(),
    })


@login_required
def group_join(request, pk):
    from .models import Group, GroupMember
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        existing = GroupMember.objects.filter(group=group, user=request.user).first()
        if existing:
            existing.is_active = not existing.is_active
            existing.save()
            if existing.is_active:
                messages.success(request, f'"{group.name}" 소모임에 참여했어요!')
            else:
                messages.info(request, f'"{group.name}" 소모임에서 나왔어요.')
        else:
            if group.member_limit and GroupMember.objects.filter(group=group, is_active=True).count() >= group.member_limit:
                messages.error(request, '참여 인원이 가득 찼어요.')
            else:
                GroupMember.objects.create(group=group, user=request.user, role='member')
                messages.success(request, f'"{group.name}" 소모임에 참여했어요!')
    return redirect('group_detail', pk=pk)


# ============================================================================
# 채팅 고정 / 삭제 API
# ============================================================================
from django.views.decorators.http import require_POST

@require_POST
@login_required
def pin_public_chat(request, msg_id):
    from django.http import JsonResponse
    if not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat = get_object_or_404(PublicChat, pk=msg_id)
    chat.is_pinned = not chat.is_pinned
    chat.save()
    return JsonResponse({'is_pinned': chat.is_pinned})

@require_POST
@login_required
def delete_public_chat(request, msg_id):
    from django.http import JsonResponse
    chat = get_object_or_404(PublicChat, pk=msg_id)
    if chat.author != request.user and not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat.is_active = False
    chat.save()
    return JsonResponse({'status': 'ok'})

@require_POST
@login_required
def pin_group_chat(request, msg_id):
    from django.http import JsonResponse
    if not request.user.is_staff:
        return JsonResponse({'error': '권한 없음'}, status=403)
    chat = get_object_or_404(GroupChat, pk=msg_id)
    chat.is_pinned = not chat.is_pinned
    chat.save()
    return JsonResponse({'is_pinned': chat.is_pinned})



# ============================================================================
# 설문조사 (업그레이드)
# ============================================================================
from .models import Survey, SurveyQuestion, SurveyResponse
import json as _json

def survey_list(request):
    active_surveys = Survey.objects.filter(status='active').select_related('creator').order_by('-created_at')
    closed_surveys = Survey.objects.filter(status='closed').select_related('creator').order_by('-created_at')
    my_surveys = Survey.objects.filter(creator=request.user).select_related('creator').order_by('-created_at') if request.user.is_authenticated else []
    # 내가 응답한 설문 ID
    responded_ids = set()
    if request.user.is_authenticated:
        responded_ids = set(SurveyResponse.objects.filter(
            respondent=request.user
        ).values_list('survey_id', flat=True))
    return render(request, 'survey/survey_list.html', {
        'active_surveys': active_surveys,
        'closed_surveys': closed_surveys,
        'my_surveys': my_surveys,
        'responded_ids': responded_ids,
    })

@login_required
def survey_create(request):
    if request.method == 'POST':
        title = request.POST.get('title','').strip()
        description = request.POST.get('description','').strip()
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        allow_multiple = request.POST.get('allow_multiple') == 'on'
        show_result = request.POST.get('show_result', 'always')
        ends_at_str = request.POST.get('ends_at','').strip()

        if not title:
            messages.error(request, '설문 제목을 입력해주세요.')
            return render(request, 'survey/survey_form.html')

        from django.utils import timezone
        import datetime
        ends_at = None
        if ends_at_str:
            try:
                ends_at = timezone.make_aware(datetime.datetime.fromisoformat(ends_at_str))
            except: pass

        # from_post 처리
        from_post_id = request.POST.get('from_post') or request.GET.get('from_post')
        source_post = None
        if from_post_id:
            try:
                source_post = Post.objects.get(pk=int(from_post_id), is_active=True)
            except: pass

        survey = Survey.objects.create(
            title=title, description=description,
            creator=request.user, is_anonymous=is_anonymous,
            allow_multiple=allow_multiple, ends_at=ends_at,
            source_post=source_post,
        )

        # 질문 파싱 (JSON으로 전달)
        questions_json = request.POST.get('questions_data', '[]')
        try:
            questions_data = _json.loads(questions_json)
        except:
            questions_data = []

        for i, q in enumerate(questions_data):
            if not q.get('text','').strip() and q.get('type') != 'section':
                continue
            SurveyQuestion.objects.create(
                survey=survey,
                text=q.get('text','').strip(),
                description=q.get('description','').strip(),
                question_type=q.get('type','single'),
                options=q.get('options',[]),
                rows=q.get('rows',[]),
                scale_min=int(q.get('scale_min',1)),
                scale_max=int(q.get('scale_max',10)),
                scale_min_label=q.get('scale_min_label',''),
                scale_max_label=q.get('scale_max_label',''),
                is_required=q.get('required',True),
                order=i,
            )

        # 원본 게시글에 자동 댓글 등록
        if source_post:
            from django.contrib.auth import get_user_model
            survey_url = f'/surveys/{survey.pk}/'
            Comment.objects.create(
                post=source_post,
                author=request.user,
                content=f'📊 이 게시글과 연관된 설문이 만들어졌어요!\n제목: {title}\n👉 설문 참여하기: {survey_url}',
            )
            messages.success(request, f'설문이 만들어지고 게시글에 안내 댓글이 등록됐어요!')
        else:
            messages.success(request, f'설문 "{title}"이 만들어졌어요!')
        return redirect('survey_detail', pk=survey.pk)

    return render(request, 'survey/survey_form.html')

def survey_detail(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.exclude(question_type='section').all() if False else survey.questions.all()
    already_responded = False
    if request.user.is_authenticated and not survey.allow_multiple:
        already_responded = SurveyResponse.objects.filter(
            survey=survey, respondent=request.user
        ).exists()
    return render(request, 'survey/survey_detail.html', {
        'survey': survey,
        'questions': questions,
        'already_responded': already_responded,
        'total': survey.total_responses,
    })

@login_required
def survey_respond(request, pk):
    from django.http import JsonResponse
    survey = get_object_or_404(Survey, pk=pk)
    if not survey.is_active:
        messages.error(request, '마감된 설문입니다.')
        return redirect('survey_detail', pk=pk)
    if not survey.allow_multiple:
        if SurveyResponse.objects.filter(survey=survey, respondent=request.user).exists():
            messages.warning(request, '이미 응답하셨습니다.')
            return redirect('survey_result', pk=pk)

    if request.method == 'POST':
        answers = {}
        for q in survey.questions.all():
            if q.question_type == 'section': continue
            key = f'q_{q.id}'
            if q.question_type == 'multiple':
                answers[str(q.id)] = request.POST.getlist(key)
            elif q.question_type == 'matrix':
                matrix_ans = {}
                for row in q.rows:
                    row_key = f'q_{q.id}_row_{row}'
                    matrix_ans[row] = request.POST.get(row_key, '')
                answers[str(q.id)] = matrix_ans
            elif q.question_type == 'rank':
                answers[str(q.id)] = request.POST.get(key, '').split(',')
            else:
                answers[str(q.id)] = request.POST.get(key, '')

        SurveyResponse.objects.create(
            survey=survey,
            respondent=request.user,
            answers=answers,
        )
        messages.success(request, '응답이 제출됐어요! 고마워요 😊')
        return redirect('survey_result', pk=pk)

    return redirect('survey_detail', pk=pk)

def survey_result(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.exclude(question_type='section')
    responses = SurveyResponse.objects.filter(survey=survey).order_by('-submitted_at')

    stats = {}
    for q in questions:
        s = {
            'id': q.id,
            'question': q.text,
            'type': q.question_type,
            'options': q.options,
            'rows': q.rows,
            'scale_min': q.scale_min,
            'scale_max': q.scale_max,
            'scale_min_label': q.scale_min_label,
            'scale_max_label': q.scale_max_label,
            'counts': {},
            'texts': [],
            'dates': [],
            'matrix': {},
            'rank_scores': {},
            'total': 0,
            'avg': 0,
        }
        total = 0
        val_sum = 0

        for resp in responses:
            ans = resp.answers.get(str(q.id))
            if not ans and ans != 0: continue
            total += 1

            if q.question_type in ('single',):
                s['counts'][ans] = s['counts'].get(ans, 0) + 1
            elif q.question_type == 'multiple':
                for a in (ans if isinstance(ans, list) else [ans]):
                    if a: s['counts'][a] = s['counts'].get(a, 0) + 1
            elif q.question_type in ('text',):
                if ans: s['texts'].append(ans)
            elif q.question_type in ('rating', 'scale'):
                try:
                    v = float(ans)
                    val_sum += v
                    k = str(int(v)) if v == int(v) else str(v)
                    s['counts'][k] = s['counts'].get(k, 0) + 1
                except: pass
            elif q.question_type in ('date', 'daterange'):
                if ans: s['dates'].append(ans if isinstance(ans, str) else str(ans))
                s['counts'][str(ans)[:10] if ans else ''] = s['counts'].get(str(ans)[:10] if ans else '', 0) + 1
            elif q.question_type == 'matrix':
                if isinstance(ans, dict):
                    for row, val in ans.items():
                        if row not in s['matrix']: s['matrix'][row] = {}
                        if val: s['matrix'][row][val] = s['matrix'][row].get(val, 0) + 1
            elif q.question_type == 'rank':
                if isinstance(ans, list):
                    for idx, item in enumerate(ans):
                        if item:
                            score = len(ans) - idx
                            s['rank_scores'][item] = s['rank_scores'].get(item, 0) + score

        s['total'] = total
        if q.question_type in ('rating','scale') and total > 0:
            s['avg'] = round(val_sum / total, 1)
        if q.question_type == 'rank' and s['rank_scores']:
            s['rank_scores'] = dict(sorted(s['rank_scores'].items(), key=lambda x: -x[1]))
        stats[q.id] = s

    # 차트 데이터
    chart_data = {}
    for qid, s in stats.items():
        if s['counts']:
            chart_data[str(qid)] = {
                'labels': list(s['counts'].keys()),
                'data': list(s['counts'].values()),
                'type': s['type'],
            }
        elif s['rank_scores']:
            chart_data[str(qid)] = {
                'labels': list(s['rank_scores'].keys()),
                'data': list(s['rank_scores'].values()),
                'type': 'rank',
            }

    # 응답자 목록 (관리자/작성자만)
    show_respondents = (request.user == survey.creator or request.user.is_staff)
    respondents = responses.select_related('respondent') if show_respondents else []

    return render(request, 'survey/survey_result.html', {
        'survey': survey,
        'stats': stats,
        'chart_data': _json.dumps(chart_data, ensure_ascii=False),
        'total_responses': responses.count(),
        'show_respondents': show_respondents,
        'respondents': respondents,
        'questions': questions,
    })

@login_required
def survey_close(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        survey.status = 'closed'
        survey.save()
        messages.success(request, '설문이 마감됐습니다.')
    return redirect('survey_result', pk=pk)

@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, '설문이 삭제됐습니다.')
        return redirect('survey_list')
    return redirect('survey_detail', pk=pk)

@login_required
def survey_export(request, pk):
    """CSV 내보내기"""
    import csv
    from django.http import HttpResponse
    survey = get_object_or_404(Survey, pk=pk)
    if survey.creator != request.user and not request.user.is_staff:
        messages.error(request, '권한이 없습니다.')
        return redirect('survey_result', pk=pk)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="survey_{pk}.csv"'
    writer = csv.writer(response)

    questions = survey.questions.exclude(question_type='section')
    header = ['응답번호', '응답일시', '응답자'] + [q.text for q in questions]
    writer.writerow(header)

    for i, resp in enumerate(SurveyResponse.objects.filter(survey=survey).select_related('respondent'), 1):
        row = [i, resp.submitted_at.strftime('%Y-%m-%d %H:%M'), resp.respondent.username if resp.respondent else '익명']
        for q in questions:
            ans = resp.answers.get(str(q.id), '')
            if isinstance(ans, list): ans = ', '.join(ans)
            elif isinstance(ans, dict): ans = ' / '.join(f"{k}:{v}" for k,v in ans.items())
            row.append(ans)
        writer.writerow(row)

    return response


# ============================================================================
# 이웃 온기 점수 (Rating)
# ============================================================================
from .models import Rating

@login_required
def rate_user(request, user_id):
    from django.http import JsonResponse
    rated_user = get_object_or_404(CustomUser, pk=user_id)
    if rated_user == request.user:
        return JsonResponse({'error': '본인은 평가할 수 없어요.'}, status=400)
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        score = int(data.get('score', 5))
        comment = data.get('comment', '').strip()
        category = data.get('category', 'general')
        score = max(1, min(5, score))
        rating, created = Rating.objects.update_or_create(
            rater=request.user, rated_user=rated_user,
            defaults={'score': score, 'comment': comment, 'category': category}
        )
        # 온기 점수 재계산 (시그널로 자동 처리)
        from hello_world.core.signals import recalculate_manners_score
        recalculate_manners_score(rated_user)
        # 평가 알림
        if created:
            Notification.objects.create(
                recipient=rated_user,
                title='따뜻한 이웃 온기를 받았어요 ❤️',
                message=f'{request.user.username}님이 온기 점수를 보내줬어요!',
                notification_type='community',
                persona='따뜻한 이웃',
            )
        rated_user.refresh_from_db()
        return JsonResponse({
            'status': 'ok',
            'created': created,
            'new_score': round(rated_user.manners_score, 1),
        })
    # GET: 현재 내 평가 조회
    my_rating = Rating.objects.filter(rater=request.user, rated_user=rated_user).first()
    return JsonResponse({
        'my_score': my_rating.score if my_rating else None,
        'my_comment': my_rating.comment if my_rating else '',
        'total_ratings': Rating.objects.filter(rated_user=rated_user).count(),
        'manners_score': round(rated_user.manners_score, 1),
    })

def user_profile(request, user_id):
    """다른 입주민 프로필 + 온기 평가"""
    profile_user = get_object_or_404(CustomUser, pk=user_id)
    ratings = Rating.objects.filter(rated_user=profile_user).order_by('-created_at')[:10]
    my_rating = None
    if request.user.is_authenticated and request.user != profile_user:
        my_rating = Rating.objects.filter(rater=request.user, rated_user=profile_user).first()
    total_activities = ActivityProof.objects.filter(user=profile_user, status='approved').count()
    user_badges = profile_user.user_badges.filter(is_displayed=True).select_related('badge')[:6]
    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'ratings': ratings,
        'my_rating': my_rating,
        'total_activities': total_activities,
        'user_badges': user_badges,
        'can_rate': request.user.is_authenticated and request.user != profile_user,
    })


# ============================================================================
# 관련 게시글 연결
# ============================================================================
@login_required
def link_related_post(request, pk):
    from django.http import JsonResponse
    post = get_object_or_404(Post, pk=pk, is_active=True)
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        target_id = data.get('target_id')
        action = data.get('action', 'add')
        try:
            target = Post.objects.get(pk=int(target_id), is_active=True)
            if action == 'add':
                post.related_posts.add(target)
                return JsonResponse({'status': 'ok', 'msg': f'"{target.title}"와 연결됐어요!'})
            else:
                post.related_posts.remove(target)
                return JsonResponse({'status': 'ok', 'msg': '연결이 해제됐어요.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    # GET: 관련 게시글 검색
    q = request.GET.get('q', '').strip()
    if q:
        results = Post.objects.filter(
            title__icontains=q, is_active=True
        ).exclude(pk=pk).exclude(related_posts=post)[:10]
        return JsonResponse({'results': [
            {'id': p.id, 'title': p.title, 'board': p.board.name, 'date': p.created_at.strftime('%m.%d')}
            for p in results
        ]})
    return JsonResponse({'results': []})


# ============================================================================
# 설문 결과 → 게시글 자동 발행
# ============================================================================
@login_required
def survey_publish_post(request, pk):
    survey = get_object_or_404(Survey, pk=pk, creator=request.user)
    if request.method == 'POST':
        # 결과 요약 자동 생성
        questions = survey.questions.exclude(question_type='section')
        responses = SurveyResponse.objects.filter(survey=survey).exclude(answers={})
        
        summary_lines = [f'📊 **{survey.title}** 설문 결과 요약\n']
        summary_lines.append(f'총 {responses.count()}명이 참여했습니다.\n')
        
        for q in questions[:5]:  # 최대 5개 질문 요약
            counts = {}
            for resp in responses:
                ans = resp.answers.get(str(q.id), '')
                if not ans: continue
                if isinstance(ans, list):
                    for a in ans:
                        if a: counts[a] = counts.get(a, 0) + 1
                else:
                    counts[str(ans)] = counts.get(str(ans), 0) + 1
            
            if counts:
                total = sum(counts.values())
                summary_lines.append(f'\n**{q.text}**')
                top = sorted(counts.items(), key=lambda x: -x[1])[:3]
                for opt, cnt in top:
                    pct = round(cnt/total*100) if total else 0
                    summary_lines.append(f'- {opt}: {cnt}명 ({pct}%)')
        
        summary_lines.append(f'\n👉 전체 결과 보기: /surveys/{survey.pk}/result/')
        content = '\n'.join(summary_lines)
        
        # 공지 게시판에 자동 발행
        board_id = request.POST.get('board_id')
        try:
            board = Board.objects.get(pk=int(board_id))
        except:
            board = Board.objects.filter(is_active=True).first()
        
        if board:
            post = Post.objects.create(
                board=board,
                author=request.user,
                title=f'[설문결과] {survey.title}',
                content=content,
                tag='설문결과',
                linked_survey=survey,
            )
            survey.source_post = survey.source_post or post
            survey.save()
            messages.success(request, f'설문 결과가 게시글로 발행됐어요!')
            return redirect('post_detail', pk=post.pk)
    
    # GET: 게시판 선택 폼
    boards = Board.objects.filter(is_active=True)
    return render(request, 'survey/survey_publish.html', {
        'survey': survey,
        'boards': boards,
    })


# ============================================================================
# 소모임 게시판
# ============================================================================
def group_post_list(request, pk):
    from .models import Group, GroupMember, GroupPost
    group = get_object_or_404(Group, pk=pk)
    is_member = GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists() if request.user.is_authenticated else False
    posts = GroupPost.objects.filter(group=group).select_related('author').order_by('-created_at')
    return render(request, 'groups/group_post_list.html', {
        'group': group, 'posts': posts, 'is_member': is_member,
    })

@login_required
def group_post_create(request, pk):
    from .models import Group, GroupMember, GroupPost
    group = get_object_or_404(Group, pk=pk)
    if not GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists():
        messages.error(request, '소모임 멤버만 글을 쓸 수 있어요.')
        return redirect('group_detail', pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if not title or not content:
            messages.error(request, '제목과 내용을 입력해주세요.')
            return render(request, 'groups/group_post_form.html', {'group': group})
        post = GroupPost.objects.create(
            group=group, author=request.user,
            title=title, content=content,
        )
        if request.FILES.get('image'):
            post.image = request.FILES['image']
            post.save()
        messages.success(request, '게시글이 등록됐어요!')
        return redirect('group_post_detail', pk=pk, post_pk=post.pk)
    return render(request, 'groups/group_post_form.html', {'group': group})

def group_post_detail(request, pk, post_pk):
    from .models import Group, GroupMember, GroupPost, GroupComment
    group = get_object_or_404(Group, pk=pk)
    post = get_object_or_404(GroupPost, pk=post_pk, group=group)
    is_member = GroupMember.objects.filter(group=group, user=request.user, is_active=True).exists() if request.user.is_authenticated else False
    comments = post.comments.select_related('author').order_by('created_at')
    if request.method == 'POST' and request.user.is_authenticated:
        content = request.POST.get('content', '').strip()
        if content:
            GroupComment.objects.create(post=post, author=request.user, content=content)
            post.comment_count = post.comments.count()
            post.save()
            messages.success(request, '댓글이 등록됐어요!')
        return redirect('group_post_detail', pk=pk, post_pk=post_pk)
    return render(request, 'groups/group_post_detail.html', {
        'group': group, 'post': post,
        'comments': comments, 'is_member': is_member,
    })

@login_required
def group_post_delete(request, pk, post_pk):
    from .models import GroupPost
    post = get_object_or_404(GroupPost, pk=post_pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, '게시글이 삭제됐어요.')
        return redirect('group_post_list', pk=pk)
    return redirect('group_post_detail', pk=pk, post_pk=post_pk)


# ============================================================================
# 채팅 미니 투표
# ============================================================================
from .models import ChatPoll

def chat_poll_create(request):
    """POST /chat/poll/create/ - /투표 명령어 처리"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)

    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options = [o.strip() for o in data.get('options', []) if o.strip()]
    chat_type = data.get('chat_type', 'public')
    group_id = data.get('group_id')

    if not question or len(options) < 2:
        return JsonResponse({'error': '질문과 선택지 2개 이상을 입력해주세요'}, status=400)

    group = None
    if group_id:
        from .models import Group
        try:
            group = Group.objects.get(pk=int(group_id))
        except: pass

    poll = ChatPoll.objects.create(
        chat_type=chat_type,
        group=group,
        creator=request.user,
        question=question,
        options=options,
        votes={opt: [] for opt in options},
    )

    # 채팅방에 투표 생성 알림 메시지 자동 전송
    poll_msg = f"📊 투표가 시작됐어요!\n질문: {question}\n" + "\n".join([f"  {i+1}. {o}" for i,o in enumerate(options)])
    if chat_type == 'public':
        PublicChat.objects.create(author=request.user, message=poll_msg)
    elif chat_type == 'group' and group:
        from .models import GroupChat
        GroupChat.objects.create(group=group, sender=request.user, message=poll_msg)

    return JsonResponse({
        'status': 'ok',
        'poll_id': poll.id,
        'question': question,
        'options': options,
    })

def chat_poll_vote(request, poll_id):
    """POST /chat/poll/<id>/vote/"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    import json
    data = json.loads(request.body)
    option = data.get('option', '').strip()

    poll = get_object_or_404(ChatPoll, pk=poll_id, is_active=True)

    if option not in poll.options:
        return JsonResponse({'error': '없는 선택지예요'}, status=400)

    # 기존 투표 제거 (한 사람 한 표)
    user_id = request.user.id
    votes = poll.votes
    for opt in votes:
        if user_id in votes[opt]:
            votes[opt].remove(user_id)

    # 새 투표 추가
    if option not in votes:
        votes[option] = []
    votes[option].append(user_id)
    poll.votes = votes
    poll.save()

    return JsonResponse({
        'status': 'ok',
        'results': poll.get_results(),
        'total': poll.total_votes,
    })

def chat_poll_list(request):
    """GET /chat/polls/?type=public&group_id=1"""
    from django.http import JsonResponse
    chat_type = request.GET.get('type', 'public')
    group_id = request.GET.get('group_id')

    polls = ChatPoll.objects.filter(chat_type=chat_type, is_active=True)
    if group_id:
        polls = polls.filter(group_id=int(group_id))
    polls = polls.order_by('-created_at')[:5]

    user_id = request.user.id if request.user.is_authenticated else None
    result = []
    for p in polls:
        my_vote = None
        for opt, voters in p.votes.items():
            if user_id in voters:
                my_vote = opt
                break
        result.append({
            'id': p.id,
            'question': p.question,
            'options': p.options,
            'results': p.get_results(),
            'total': p.total_votes,
            'my_vote': my_vote,
            'creator': p.creator.nickname or p.creator.username,
            'created_at': p.created_at.strftime('%H:%M'),
            'is_active': p.is_active,
        })

    return JsonResponse({'polls': result})


# ============================================================================
# 채팅 미니 투표
# ============================================================================
from .models import ChatPoll

def chat_poll_create(request):
    """POST /chat/poll/create/ - /투표 명령어 처리"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청'}, status=400)

    import json
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    options = [o.strip() for o in data.get('options', []) if o.strip()]
    chat_type = data.get('chat_type', 'public')
    group_id = data.get('group_id')

    if not question or len(options) < 2:
        return JsonResponse({'error': '질문과 선택지 2개 이상을 입력해주세요'}, status=400)

    group = None
    if group_id:
        from .models import Group
        try:
            group = Group.objects.get(pk=int(group_id))
        except: pass

    poll = ChatPoll.objects.create(
        chat_type=chat_type,
        group=group,
        creator=request.user,
        question=question,
        options=options,
        votes={opt: [] for opt in options},
    )

    # 채팅방에 투표 생성 알림 메시지 자동 전송
    poll_msg = f"📊 투표가 시작됐어요!\n질문: {question}\n" + "\n".join([f"  {i+1}. {o}" for i,o in enumerate(options)])
    if chat_type == 'public':
        PublicChat.objects.create(author=request.user, message=poll_msg)
    elif chat_type == 'group' and group:
        from .models import GroupChat
        GroupChat.objects.create(group=group, sender=request.user, message=poll_msg)

    return JsonResponse({
        'status': 'ok',
        'poll_id': poll.id,
        'question': question,
        'options': options,
    })

def chat_poll_vote(request, poll_id):
    """POST /chat/poll/<id>/vote/"""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)

    import json
    data = json.loads(request.body)
    option = data.get('option', '').strip()

    poll = get_object_or_404(ChatPoll, pk=poll_id, is_active=True)

    if option not in poll.options:
        return JsonResponse({'error': '없는 선택지예요'}, status=400)

    # 기존 투표 제거 (한 사람 한 표)
    user_id = request.user.id
    votes = poll.votes
    for opt in votes:
        if user_id in votes[opt]:
            votes[opt].remove(user_id)

    # 새 투표 추가
    if option not in votes:
        votes[option] = []
    votes[option].append(user_id)
    poll.votes = votes
    poll.save()

    return JsonResponse({
        'status': 'ok',
        'results': poll.get_results(),
        'total': poll.total_votes,
    })

def chat_poll_list(request):
    """GET /chat/polls/?type=public&group_id=1"""
    from django.http import JsonResponse
    chat_type = request.GET.get('type', 'public')
    group_id = request.GET.get('group_id')

    polls = ChatPoll.objects.filter(chat_type=chat_type, is_active=True)
    if group_id:
        polls = polls.filter(group_id=int(group_id))
    polls = polls.order_by('-created_at')[:5]

    user_id = request.user.id if request.user.is_authenticated else None
    result = []
    for p in polls:
        my_vote = None
        for opt, voters in p.votes.items():
            if user_id in voters:
                my_vote = opt
                break
        result.append({
            'id': p.id,
            'question': p.question,
            'options': p.options,
            'results': p.get_results(),
            'total': p.total_votes,
            'my_vote': my_vote,
            'creator': p.creator.nickname or p.creator.username,
            'created_at': p.created_at.strftime('%H:%M'),
            'is_active': p.is_active,
        })

    return JsonResponse({'polls': result})


def community_stats(request):
    """단지 통계 대시보드"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    from .models import CustomUser, Post, Comment, Survey, SurveyResponse, Event, Group, GroupMember, Letter, DirectMessage, PublicChat

    now = timezone.now()
    month_ago = now - timedelta(days=30)
    week_ago  = now - timedelta(days=7)

    # 회원
    total_users   = CustomUser.objects.filter(is_active=True).count()
    new_users     = CustomUser.objects.filter(date_joined__gte=month_ago).count()

    # 게시글/댓글
    total_posts    = Post.objects.count()
    week_posts     = Post.objects.filter(created_at__gte=week_ago).count()
    total_comments = Comment.objects.count()

    # 설문
    total_surveys   = Survey.objects.count()
    total_responses = SurveyResponse.objects.count()

    # 봉사
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_time__gte=now).count()

    # 소모임
    total_groups  = Group.objects.filter(is_active=True).count()
    total_members = GroupMember.objects.count()

    # 채팅 활성도 (최근 7일)
    week_public = PublicChat.objects.filter(created_at__gte=week_ago).count()
    week_dm     = DirectMessage.objects.filter(created_at__gte=week_ago).count()
    week_letter = Letter.objects.filter(created_at__gte=week_ago).count()

    # 활동 랭킹 TOP5 (게시글 기준)
    top_users = CustomUser.objects.annotate(
        post_count=Count("posts")
    ).order_by("-post_count")[:5]

    # 월별 신규 가입자 (최근 6개월)
    monthly_joins = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30*i)
        cnt = CustomUser.objects.filter(
            date_joined__year=d.year,
            date_joined__month=d.month
        ).count()
        monthly_joins.append({"month": d.strftime("%m월"), "count": cnt})

    return render(request, "stats_dashboard.html", {
        "total_users": total_users, "new_users": new_users,
        "total_posts": total_posts, "week_posts": week_posts,
        "total_comments": total_comments,
        "total_surveys": total_surveys, "total_responses": total_responses,
        "total_events": total_events, "upcoming_events": upcoming_events,
        "total_groups": total_groups, "total_members": total_members,
        "week_public": week_public, "week_dm": week_dm, "week_letter": week_letter,
        "top_users": top_users,
        "monthly_joins": monthly_joins,
    })


def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)
