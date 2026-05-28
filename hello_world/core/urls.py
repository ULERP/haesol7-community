from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts',   views.PostViewSet,   basename='post')
router.register(r'groups',  views.GroupViewSet,  basename='group')
router.register(r'meetups', views.MeetupViewSet, basename='meetup')

urlpatterns = [
    # 메인
    path('', views.index, name='index'),

    # 회원
    path('accounts/login/',  views.custom_login, name='login'),
    path('accounts/signup/', views.signup,        name='signup'),
    path('mypage/',          views.mypage,         name='mypage'),
    path('mypage/edit/',     views.profile_edit,   name='profile_edit'),

    # 게시판
    path('boards/',                              views.board_list,       name='board_list'),
    path('board/<int:board_id>/',                views.board_detail,     name='board_detail'),
    path('board/<int:board_id>/write/',          views.post_write,       name='post_write'),
    path('posts/',                               views.post_list,        name='post_list'),
    path('posts/<int:pk>/',                      views.post_detail,      name='post_detail'),
    path('posts/create/',                        views.board_post_create,name='post_create_board'),
    path('post/create/',                         views.post_create,      name='post_create'),
    path('post/<int:pk>/edit/',                  views.post_edit,        name='post_edit'),
    path('post/<int:pk>/delete/',                views.post_delete,      name='post_delete'),
    path('post/<int:post_id>/like/',             views.post_like,        name='post_like'),
    path('post/<int:post_id>/comment/',          views.comment_create,   name='comment_create'),

    # 활동 인증
    path('activity/',        views.activity_list,         name='activity_list'),
    path('activity/submit/', views.activity_proof_submit, name='activity_proof_submit'),
    path('activity/list/',   views.activity_proof_list,   name='activity_proof_list'),
    path('volunteer/',           views.volunteer_calendar, name='volunteer_calendar'),
    path('volunteer/<int:pk>/',  views.volunteer_detail,   name='volunteer_detail'),
    path('volunteer/<int:pk>/join/', views.volunteer_join, name='volunteer_join'),

    # API
    path('search/', views.search, name='search'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/count/', views.notification_count, name='notification_count'),
    path('api/', include(router.urls)),
]
