from .models import Board

def boards_context(request):
    """사이드바용 게시판 목록"""
    boards = Board.objects.filter(is_active=True).exclude(board_type__in=['trade','qna','gallery']).order_by('order', 'id')
    return {
        'sb_boards': boards,
    }
