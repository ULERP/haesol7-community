from django.urls import path, include
from django.contrib.auth.views import LogoutView
from . import views_letter, views_verify, views_complaint
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts',   views.PostViewSet,   basename='post')
router.register(r'groups',  views.GroupViewSet,  basename='group')
router.register(r'meetups', views.MeetupViewSet, basename='meetup')

urlpatterns = [
    path('accounts/password-reset/',                    views.password_reset_page,  name='password_reset_page'),
    path('accounts/password-reset/get-question/',        views.pw_get_question,       name='pw_get_question'),
    path('accounts/password-reset/verify-answer/',       views.pw_verify_answer,      name='pw_verify_answer'),
    path('accounts/password-reset/do-reset/',            views.pw_do_reset,           name='pw_do_reset'),
    path('accounts/password-reset/send-email/',          views.pw_send_email,         name='pw_send_email'),
    path('accounts/password-reset/email-confirm/',       views.pw_email_confirm,      name='pw_email_confirm'),
    path('admin-tools/members/',            views.admin_member_manage, name='admin_member_manage'),
    path('admin-tools/members/pw-reset/',   views.admin_pw_reset,      name='admin_pw_reset'),
    path('admin-tools/members/grade/',      views.admin_grade_change,  name='admin_grade_change'),
    path('admin-tools/members/toggle/',     views.admin_toggle_active, name='admin_toggle_active'),
    path('admin-tools/logs/',               views.admin_action_log,    name='admin_action_log'),
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
    path('calendar/', views.integrated_calendar, name='integrated_calendar'),
    path('calendar/create/', views.calendar_event_create, name='calendar_event_create'),
    path('calendar/<int:pk>/delete/', views.calendar_event_delete, name='calendar_event_delete'),
    path('calendar/<int:pk>/approve/', views.calendar_event_approve, name='calendar_event_approve'),

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
    path('groups/<int:pk>/member-action/',                 views.group_member_action, name='group_member_action'),
    path('groups/<int:pk>/dissolve/',                      views.group_dissolve,      name='group_dissolve'),
    path('groups/<int:pk>/posts/',                         views.group_post_list,   name='group_post_list'),
    path('groups/<int:pk>/posts/create/',                  views.group_post_create, name='group_post_create'),
    path('groups/<int:pk>/posts/<int:post_pk>/',           views.group_post_detail, name='group_post_detail'),
    path('groups/<int:pk>/posts/<int:post_pk>/delete/',    views.group_post_delete, name='group_post_delete'),

    path('search/',                        views.search,               name='search'),
    path('chat/public/',                   views.public_chat,          name='public_chat'),
    path('chat/public/messages/',          views.public_chat_messages, name='public_chat_messages'),
    path('chat/public/<int:msg_id>/pin/',    views.pin_public_chat,      name='pin_public_chat'),
    path('chat/public/<int:msg_id>/delete/', views.delete_public_chat,   name='delete_public_chat'),
    path('chat/dm/<int:user_id>/',         views.direct_message,       name='direct_message'),
    path('chat/dm/<int:user_id>/messages/', views.dm_messages,         name='dm_messages'),
    path('chat/dm/list/',                  views.dm_list,              name='dm_list'),
    path('chat/group/<int:group_id>/',     views.group_chat,           name='group_chat'),
    path('chat/group/<int:group_id>/messages/', views.group_chat_messages, name='group_chat_messages'),
    path('notifications/',                 views.notification_list,    name='notification_list'),
    path('notifications/count/',           views.notification_count,   name='notification_count'),
    path('api/', include(router.urls)),
    path('stats/', views.community_stats, name='community_stats'),

    # 쪽지함
    path('letters/', views_letter.letter_inbox, name='letter_inbox'),
    path('letters/sent/', views_letter.letter_sent, name='letter_sent'),
    path('letters/write/', views_letter.letter_write, name='letter_write'),
    path('letters/write/<int:receiver_id>/', views_letter.letter_write, name='letter_write_to'),
    path('letters/<int:pk>/', views_letter.letter_detail, name='letter_detail'),
    path('letters/<int:pk>/reply/', views_letter.letter_reply, name='letter_reply'),
    path('letters/<int:pk>/delete/', views_letter.letter_delete, name='letter_delete'),

    # 입주민 인증
    path('verify/', views_verify.verify_request, name='verify_request'),
    path('verify/admin/', views_verify.verify_admin, name='verify_admin'),
    path('verify/approve/<int:user_id>/', views_verify.verify_approve, name='verify_approve'),
    path('verify/reject/<int:user_id>/', views_verify.verify_reject, name='verify_reject'),

    # 민원/건의
    path('complaints/', views_complaint.complaint_list, name='complaint_list'),
    path('complaints/create/', views_complaint.complaint_create, name='complaint_create'),
    path('complaints/<int:pk>/', views_complaint.complaint_detail, name='complaint_detail'),
    path('complaints/admin/', views_complaint.complaint_admin, name='complaint_admin'),
    path('complaints/<int:pk>/reply/', views_complaint.complaint_reply, name='complaint_reply'),


    # 봉사 인증서 PDF
    path('certificate/<int:user_id>/', views.certificate_pdf, name='certificate_pdf'),
    path('certificate/my/', views.my_certificate, name='my_certificate'),
    # 빠른 공지
    path('notices/', views_complaint.notice_list, name='notice_list'),
    path('notices/create/', views_complaint.notice_create, name='notice_create'),
    path('notices/<int:pk>/delete/', views_complaint.notice_delete, name='notice_delete'),
]
