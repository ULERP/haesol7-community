def global_settings(request):
    return {
        'app_name': 'Haesol7 Community',
    }

def active_boards(request):
    try:
        from hello_world.core.models import Board
        boards = Board.objects.filter(is_active=True).order_by('order')
    except Exception:
        boards = []
    return {'active_boards': boards}
