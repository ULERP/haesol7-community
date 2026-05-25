import os
import sys
from datetime import timedelta

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'haesol7_project.settings.development')

    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from hello_world.core.models import (
        Board,
        Post,
        Event,
        Poll,
        Choice,
        Activity,
        ActivityVerification,
    )

    User = get_user_model()

    print('🚀 populate_db: 샘플 데이터 생성 시작')

    # 사용자
    admin_user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@haesol7.com',
            'first_name': '해솔7',
            'last_name': '관리자',
            'unit_number': '101동 1001호',
        }
    )
    if admin_user.pk and not admin_user.is_superuser:
        admin_user.set_password('admin123!')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

    sample_users = [
        {'username': 'user1', 'email': 'user1@haesol7.com', 'first_name': '김지킴', 'unit_number': '102동 1002호'},
        {'username': 'user2', 'email': 'user2@haesol7.com', 'first_name': '이순찰', 'unit_number': '103동 1003호'},
        {'username': 'user3', 'email': 'user3@haesol7.com', 'first_name': '박환경', 'unit_number': '104동 1004호'},
    ]
    for user_data in sample_users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'unit_number': user_data['unit_number'],
            }
        )
        if created:
            user.set_password('test1234')
            user.save()

    print('✅ 사용자 생성/확인 완료')

    # 게시판
    boards = [
        {
            'name': '공지 및 행정',
            'board_type': 'notice',
            'description': '단지 공지 및 행정 소식을 공유합니다.',
            'write_permission': 'staff',
            'allowed_tags': '지킴이공지,주민공지,단지소식,행정/시책',
            'icon': 'fas fa-bullhorn',
            'order': 1,
        },
        {
            'name': '우리 동네 소통',
            'board_type': 'free',
            'description': '주민이 자유롭게 소통하고 나눌 수 있는 공간입니다.',
            'write_permission': 'member',
            'allowed_tags': '자유,나눔,장터,맛집',
            'icon': 'fas fa-comments',
            'order': 2,
        },
        {
            'name': '생활 정보 공유',
            'board_type': 'free',
            'description': '생활 정보, 수리, 육아, 운동 등에 관한 실용 정보를 공유합니다.',
            'write_permission': 'member',
            'allowed_tags': '에티켓,수리보수,재활용,육아,학습,운동',
            'icon': 'fas fa-lightbulb',
            'order': 3,
        },
        {
            'name': '여가와 활동',
            'board_type': 'event',
            'description': '취미, 여행, 영상 등 여가 활동 아이디어를 나눕니다.',
            'write_permission': 'member',
            'allowed_tags': '취미,여행,영상',
            'icon': 'fas fa-camera-retro',
            'order': 4,
        },
        {
            'name': '지킴이 아카이브',
            'board_type': 'archive',
            'description': '운영진 양식, 회의록, 활동 기록을 보관하는 아카이브입니다.',
            'write_permission': 'staff',
            'allowed_tags': '모집,활동기록,회의록,양식',
            'icon': 'fas fa-archive',
            'order': 5,
        },
        {
            'name': '건의와 FAQ',
            'board_type': 'suggestion',
            'description': '입주민 건의와 FAQ를 모아 소통하는 공간입니다.',
            'write_permission': 'member',
            'allowed_tags': '건의,질문,FAQ',
            'icon': 'fas fa-question-circle',
            'order': 6,
        },
    ]
    board_objs = {}
    for board_info in boards:
        board, _ = Board.objects.update_or_create(
            name=board_info['name'],
            defaults={
                'board_type': board_info['board_type'],
                'description': board_info['description'],
                'write_permission': board_info['write_permission'],
                'allowed_tags': board_info['allowed_tags'],
                'icon': board_info['icon'],
                'order': board_info['order'],
                'is_active': True,
            }
        )
        board_objs[board_info['name']] = board

    print('✅ 게시판 생성/확인 완료')

    # 샘플 게시글 및 이벤트
    welcome_post, _ = Post.objects.get_or_create(
        board=board_objs['공지사항'],
        author=admin_user,
        title='새로운 커뮤니티 플랫폼을 환영합니다',
        defaults={
            'content': '해솔마을 7단지 커뮤니티 게시판에 오신 것을 환영합니다! 공지, 자유글, 봉사활동, 투표 등 다양한 기능을 이용해보세요.',
            'tag': '공지',
            'is_pinned': True,
            'is_anonymous': False,
        }
    )

    volunteer_post, _ = Post.objects.get_or_create(
        board=board_objs['봉사활동'],
        author=User.objects.get(username='user1'),
        title='5월 단지 환경 정화 활동 참여자 모집',
        defaults={
            'content': '이번 주 토요일 오전 10시에 단지 공원에서 환경 정화 활동을 진행합니다. 참여하실 분은 댓글로 남겨주세요.',
            'tag': '모집',
            'is_anonymous': False,
        }
    )

    event_post, _ = Post.objects.get_or_create(
        board=board_objs['행사'],
        author=User.objects.get(username='user2'),
        title='5월 주민 소통의 날 행사 안내',
        defaults={
            'content': '5월 28일 화요일 오후 5시에 주민 소통의 날 행사를 개최합니다. 많은 참여 부탁드립니다.',
            'tag': '행사',
            'is_anonymous': False,
        }
    )

    poll_post, _ = Post.objects.get_or_create(
        board=board_objs['투표'],
        author=User.objects.get(username='user3'),
        title='단지 내 공용 자전거 보관소 위치 선호 투표',
        defaults={
            'content': '공용 자전거 보관소 위치를 아래 선택지 중에서 골라주세요.',
            'tag': '투표',
            'is_anonymous': False,
        }
    )

    print('✅ 게시글 샘플 생성/확인 완료')

    # Event 연결
    event, created = Event.objects.get_or_create(
        post=event_post,
        defaults={
            'title': '5월 주민 소통의 날',
            'start_date': timezone.now() + timedelta(days=6, hours=17),
            'end_date': timezone.now() + timedelta(days=6, hours=19),
            'location': '단지 커뮤니티 센터',
        }
    )
    if created:
        print('✅ 이벤트 생성 완료')

    # Poll 및 Choices 연결
    poll, created = Poll.objects.get_or_create(
        post=poll_post,
        defaults={
            'question': '공용 자전거 보관소의 최적 위치는 어디라고 생각하시나요?',
        }
    )
    if created:
        Choice.objects.get_or_create(poll=poll, label='A동 중앙 정문 근처', defaults={'order': 1})
        Choice.objects.get_or_create(poll=poll, label='B동 옆 공터', defaults={'order': 2})
        Choice.objects.get_or_create(poll=poll, label='C동 어린이 놀이터 옆', defaults={'order': 3})
        print('✅ 투표 및 선택지 생성 완료')

    # ActivityVerification 샘플
    activity = Activity.objects.first()
    if activity is None:
        activity = Activity.objects.create(
            name='커뮤니티 정화 봉사',
            activity_type='cleaning',
            description='단지 내 쓰레기 줍기 및 분리 배출 안내',
            points_per_hour=10,
            base_points=50,
        )

    verification, created = ActivityVerification.objects.get_or_create(
        submitter=User.objects.get(username='user1'),
        activity=activity,
        activity_date=timezone.now().date(),
        defaults={
            'content': '단지 공원 주변 쓰레기를 수거하고 분리수거 안내를 진행했습니다.',
            'approved': True,
            'approved_by': admin_user,
            'approved_at': timezone.now(),
            'notes': '깨끗하게 잘 정리해주셨습니다.',
        }
    )
    if created:
        print('✅ 활동 인증 샘플 생성 완료')

    print('✨ populate_db 완료')
