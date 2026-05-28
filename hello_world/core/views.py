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
    boards = Board.objects.filter(is_active=True).order_by('order')
    recent_posts = Post.objects.filter(is_active=True).order_by('-created_at')[:10]
    upcoming_events = Activity.objects.filter(is_active=True).order_by('created_at')[:5]
    from .models import Badge
    return render(request, 'index.html', {
        'boards': boards,
        'recent_posts': recent_posts,
        'upcoming_events': upcoming_events,
        'badges_count': Badge.objects.filter(is_active=True).count(),
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
    my_posts    = Post.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    my_comments = Comment.objects.filter(author=user, is_active=True).order_by('-created_at')[:5]
    user_grade_name = get_user_grade(user)
    try:
        user_grade = MemberGrade.objects.get(name=str(user_grade_name)) if user_grade_name else None
    except:
        user_grade = None
    total_activities = ActivityProof.objects.filter(user=user, status='approved').count()
    return render(request, 'mypage.html', {
        'user': user,
        'my_posts': my_posts,
        'my_comments': my_comments,
        'user_grade': user_grade,
        'total_activities': total_activities,
        'total_points': user.mileage_points,
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
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'can_comment': check_board_permission(request.user, post.board, 'comment'),
        'can_write':   check_board_permission(request.user, post.board, 'write'),
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
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        user.first_name    = request.POST.get('first_name', '')
        user.unit_number   = request.POST.get('unit_number', '')
        user.phone_number  = request.POST.get('phone_number', '')
        user.introduction  = request.POST.get('introduction', '')
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, '프로필이 수정됐습니다!')
        return redirect('mypage')
    return render(request, 'profile_edit.html', {'user': user})


@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        user.first_name   = request.POST.get('first_name', '')
        user.unit_number  = request.POST.get('unit_number', '')
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
