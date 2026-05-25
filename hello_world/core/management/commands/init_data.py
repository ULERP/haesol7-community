from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hello_world.core.models import Badge, Activity
from hello_world.core.signals import seed_initial_badges, seed_initial_activities

User = get_user_model()


class Command(BaseCommand):
    help = '초기 데이터 생성 및 관리자 계정 생성'

    def handle(self, *args, **options):
        self.stdout.write('🚀 초기 데이터 생성 시작...\n')
        
        # 1. 배지 생성
        self.stdout.write('📛 배지 생성 중...')
        seed_initial_badges()
        badges = Badge.objects.all().count()
        self.stdout.write(self.style.SUCCESS(f'✅ {badges}개의 배지 생성됨'))
        
        # 2. 활동 카테고리 생성
        self.stdout.write('🏃 활동 카테고리 생성 중...')
        seed_initial_activities()
        activities = Activity.objects.all().count()
        self.stdout.write(self.style.SUCCESS(f'✅ {activities}개의 활동 생성됨'))
        
        # 3. 관리자 계정 생성
        self.stdout.write('👤 관리자 계정 생성 중...')
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@haesol7.com',
                password='admin123!',
                first_name='해솔7',
                last_name='관리자',
                unit_number='101동 1001호'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ 관리자 계정 생성됨 (username: admin, password: admin123!)')
            )
        else:
            self.stdout.write('⏭️  관리자 계정이 이미 존재합니다')
        
        # 4. 테스트 사용자 생성
        self.stdout.write('👥 테스트 사용자 생성 중...')
        test_users = [
            {'username': 'user1', 'name': '김지킴', 'unit': '102동 1002호'},
            {'username': 'user2', 'name': '이순찰', 'unit': '103동 1003호'},
            {'username': 'user3', 'name': '박환경', 'unit': '104동 1004호'},
        ]
        
        created_count = 0
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(
                    username=user_data['username'],
                    email=f"{user_data['username']}@haesol7.com",
                    password='test1234',
                    first_name=user_data['name'],
                    unit_number=user_data['unit']
                )
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ {created_count}개의 테스트 사용자 생성됨'))
        
        self.stdout.write('\n' + self.style.SUCCESS('✨ 초기 데이터 생성 완료!'))
        self.stdout.write('\n📝 다음 단계:')
        self.stdout.write('1. 관리자 로그인: http://localhost:8000/admin/')
        self.stdout.write('   - Username: admin')
        self.stdout.write('   - Password: admin123!')
        self.stdout.write('2. API 테스트: http://localhost:8000/api/')
        self.stdout.write('3. 개발 서버 시작: python manage.py runserver\n')
