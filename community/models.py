from django.db import models
from core.models import TenantModel
class Board(TenantModel):
    name = models.CharField("게시판명", max_length=50)
    description = models.TextField("설명", blank=True)
    icon = models.CharField("아이콘", max_length=50, default='fas fa-clipboard')
    order = models.PositiveIntegerField("순서", default=0)
    class Meta:
        verbose_name = "게시판"
        ordering = ['order']
    def __str__(self):
        return self.name
class Post(TenantModel):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField("제목", max_length=200)
    content = models.TextField("내용")
    tag = models.CharField("머리말", max_length=30, blank=True)
    is_pinned = models.BooleanField("상단고정", default=False)
    view_count = models.PositiveIntegerField("조회수", default=0)
    class Meta:
        verbose_name = "게시글"
        ordering = ['-is_pinned', '-created_at']
    def __str__(self):
        return self.title
class Comment(TenantModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField("내용")
    class Meta:
        verbose_name = "댓글"
        ordering = ['created_at']
