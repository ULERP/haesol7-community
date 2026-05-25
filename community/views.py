from django.shortcuts import render, get_object_or_404
from .models import Board, Post
def index(request):
    boards = Board.objects.filter(is_active=True).order_by('order')
    recent_posts = Post.objects.filter(is_active=True).order_by('-created_at')[:10]
    return render(request, 'community/index.html', {'boards': boards, 'recent_posts': recent_posts})
def board_detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id, is_active=True)
    posts = Post.objects.filter(board=board, is_active=True)
    return render(request, 'community/board_detail.html', {'board': board, 'posts': posts})
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id, is_active=True)
    Post.objects.filter(pk=post_id).update(view_count=post.view_count+1)
    return render(request, 'community/post_detail.html', {'post': post})
