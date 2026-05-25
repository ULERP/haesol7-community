from django.urls import path
from . import views
app_name = 'community'
urlpatterns = [
    path('', views.index, name='index'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
]
