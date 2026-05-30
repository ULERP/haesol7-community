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

def verification_status(request):
    if request.user.is_authenticated:
        return {'user_is_verified': request.user.is_verified}
    return {'user_is_verified': False}
