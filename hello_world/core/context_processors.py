import random

def common_context(request):
    from .models import Post, Survey, Meetup
    from django.utils import timezone

    # 최신 공지
    try:
        latest_notices = list(Post.objects.filter(
            is_active=True,
            tag__in=['지킴이공지','주민공지','단지소식','공지']
        ).order_by('-created_at')[:3])
    except:
        latest_notices = []

    # 최근 관리문서
    try:
        from community.models import ManagementDocument
        recent_docs = list(ManagementDocument.objects.order_by('-created_at')[:2])
    except:
        recent_docs = []

    # 봉사 일정
    try:
        upcoming_meetups = list(Meetup.objects.filter(
            scheduled_at__gte=timezone.now(),
            status__in=['recruiting','confirmed']
        ).order_by('scheduled_at')[:3])
    except:
        upcoming_meetups = []

    # 진행 중인 설문
    try:
        active_surveys = list(Survey.objects.filter(status='active').order_by('-created_at')[:3])
    except:
        active_surveys = []

    # 랜덤 봉사 활동 추천 (3개 랜덤)
    all_activities = [
        {'icon': '🌳', 'name': '단지 환경 정비', 'desc': '쾌적한 단지를 함께 만들어요'},
        {'icon': '🐕', 'name': '펫 매너 캠페인', 'desc': '반려동물 에티켓을 함께해요'},
        {'icon': '🌙', 'name': '야간 안전 순찰', 'desc': '안전한 단지를 지켜요'},
        {'icon': '🌻', 'name': '화단 가꾸기', 'desc': '아름다운 단지를 만들어요'},
        {'icon': '♻️', 'name': '분리수거 캠페인', 'desc': '올바른 분리수거를 함께해요'},
        {'icon': '🤝', 'name': '이웃 돕기', 'desc': '어려운 이웃을 도와요'},
    ]
    random_activities = random.sample(all_activities, min(3, len(all_activities)))

    return {
        'latest_notices': latest_notices,
        'recent_docs': recent_docs,
        'upcoming_meetups': upcoming_meetups,
        'active_surveys': active_surveys,
        'random_activities': random_activities,
    }
