# community 앱은 hello_world.core.models의 모델을 그대로 사용합니다.
from hello_world.core.models import (
    Board, Post, Comment, PostLike, PostImage,
    ManagementDocument, Trade, Poll, Event,
    Category, Choice,
)

__all__ = [
    'Board', 'Post', 'Comment', 'PostLike', 'PostImage',
    'ManagementDocument', 'Trade', 'Poll', 'Event',
    'Category', 'Choice',
]
