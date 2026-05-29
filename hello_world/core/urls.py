from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views_letter
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts',   views.PostViewSet,   basename='post')
router.register(r'groups',  views.GroupViewSet,  basename='group')
router.register(r'meetups', views.MeetupViewSet, basename='meetup')

urlpatterns = [
    path('', views.index, name='index'),

    path('accounts/login/',  views.custom_login, name='login'),
    path('accounts/signup/', views.signup,        name='signup'),
    path('login/', lambda r: __import__('django.shortcuts', fromlist=['redirect']).redirect('/accounts/login/'), name='login_redirect'),
    path('signup/', lambda r: __import__('django.shortcuts', fromlist=['redirect']).redirect('/accounts/signup/'), name='signup_redirect'),
    path('accounts/logout/', LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('mypage/',          views.mypage,         name='mypage'),
    path('mypage/edit/',     views.profile_edit,   name='profile_edit'),

    path('boards/',                              views.board_list,        name='board_list'),
    path('board/<int:board_id>/',                views.board_detail,      name='board_detail'),
    path('board/<int:board_id>/write/',          views.post_write,        name='post_write'),
    path('posts/',                               views.post_list,         name='post_list'),
    path('posts/<int:pk>/',                      views.post_detail,       name='post_detail'),
    path('posts/create/',                        views.board_post_create, name='post_create_board'),
    path('post/create/',                         views.post_create,       name='post_create'),
    path('post/<int:pk>/edit/',                  views.post_edit,         name='post_edit'),
    path('post/<int:pk>/delete/',                views.post_delete,       name='post_delete'),
    path('post/<int:post_id>/like/',             views.post_like,         name='post_like'),
    path('post/<int:post_id>/comment/',          views.comment_create,    name='comment_create'),

    path('activity/',        views.activity_list,          name='activity_list'),
    path('activity/submit/', views.activity_proof_submit,  name='activity_proof_submit'),
    path('activity/list/',   views.activity_proof_list,    name='activity_proof_list'),
    path('volunteer/',               views.volunteer_calendar, name='volunteer_calendar'),
    path('volunteer/<int:pk>/',      views.volunteer_detail,   name='volunteer_detail'),
    path('volunteer/<int:pk>/join/', views.volunteer_join,     name='volunteer_join'),

    path('post/<int:pk>/link/', views.link_related_post, name='link_related_post'),

    path('chat/poll/create/',              views.chat_poll_create, name='chat_poll_create'),
    path('chat/poll/<int:poll_id>/vote/',  views.chat_poll_vote,   name='chat_poll_vote'),
    path('chat/polls/',                    views.chat_poll_list,   name='chat_poll_list'),

    path('users/<int:user_id>/rate/', views.rate_user,    name='rate_user'),
    path('users/<int:user_id>/',      views.user_profile, name='user_profile'),

    path('surveys/',                   views.survey_list,    name='survey_list'),
    path('surveys/create/',            views.survey_create,  name='survey_create'),
    path('surveys/<int:pk>/',          views.survey_detail,  name='survey_detail'),
    path('surveys/<int:pk>/respond/',  views.survey_respond, name='survey_respond'),
    path('surveys/<int:pk>/result/',   views.survey_result,  name='survey_result'),
    path('surveys/<int:pk>/close/',    views.survey_close,   name='survey_close'),
    path('surveys/<int:pk>/delete/',   views.survey_delete,  name='survey_delete'),
    path('surveys/<int:pk>/export/',   views.survey_export,  name='survey_export'),

    path('groups/',                                        views.group_list,        name='group_list'),
    path('groups/create/',                                 views.group_create,      name='group_create'),
    path('groups/<int:pk>/',                               views.group_detail,      name='group_detail'),
    path('groups/<int:pk>/join/',                          views.group_join,        name='group_join'),
    path('groups/<int:pk>/posts/',                         views.group_post_list,   name='group_post_list'),
    path('groups/<int:pk>/posts/create/',                  views.group_post_create, name='group_post_create'),
    path('groups/<int:pk>/posts/<int:post_pk>/',           views.group_post_detail, name='group_post_detail'),
    path('groups/<int:pk>/posts/<int:post_pk>/delete/',    views.group_post_delete, name='group_post_delete'),

    path('search/',                        views.search,               name='search'),
    path('chat/public/',                   views.public_chat,          name='public_chat'),
    path('chat/public/messages/',          views.public_chat_messages, name='public_chat_messages'),
    path('chat/dm/<int:user_id>/',         views.direct_message,       name='direct_message'),
    path('chat/dm/<int:user_id>/messages/', views.dm_messages,         name='dm_messages'),
    path('chat/dm/list/',                  views.dm_list,              name='dm_list'),
    path('chat/group/<int:group_id>/',     views.group_chat,           name='group_chat'),
    path('chat/group/<int:group_id>/messages/', views.group_chat_messages, name='group_chat_messages'),
    path('chatbot/',                       views.chatbot,              name='chatbot'),
    path('chatbot/ask/',                   views.chatbot_ask,          name='chatbot_ask'),
    path('notifications/',                 views.notification_list,    name='notification_list'),
    path('notifications/count/',           views.notification_count,   name='notification_count'),
    path('api/', include(router.urls)),

    # 쪽지함
    path('letters/', views_letter.letter_inbox, name='letter_inbox'),
    path('letters/sent/', views_letter.letter_sent, name='letter_sent'),
    path('letters/write/', views_letter.letter_write, name='letter_write'),
    path('letters/write/<int:receiver_id>/', views_letter.letter_write, name='letter_write_to'),
    path('letters/<int:pk>/', views_letter.letter_detail, name='letter_detail'),
    path('letters/<int:pk>/reply/', views_letter.letter_reply, name='letter_reply'),
    path('letters/<int:pk>/delete/', views_letter.letter_delete, name='letter_delete'),
]
