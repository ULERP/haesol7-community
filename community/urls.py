from django.urls import path
from . import views
app_name = 'community'
urlpatterns = [
    path('', views.index, name='index'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
]
from .views import (
    ManagementDocumentListView, ManagementDocumentDetailView,
    ManagementDocumentCreateView, ManagementDocumentUpdateView,
    ManagementDocumentDeleteView,
)

urlpatterns += [
    path('docs/', ManagementDocumentListView.as_view(), name='management_doc_list'),
    path('docs/<int:pk>/', ManagementDocumentDetailView.as_view(), name='management_doc_detail'),
    path('docs/create/', ManagementDocumentCreateView.as_view(), name='management_doc_create'),
    path('docs/<int:pk>/edit/', ManagementDocumentUpdateView.as_view(), name='management_doc_edit'),
    path('docs/<int:pk>/delete/', ManagementDocumentDeleteView.as_view(), name='management_doc_delete'),
]