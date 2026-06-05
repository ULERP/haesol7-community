from django import forms
from .models import Post, Trade, Event, ActivityProof

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'tag', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목을 입력하세요'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': '내용을 입력하세요'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'title': '제목', 'content': '내용', 'tag': '말머리', 'is_anonymous': '익명으로 작성'}

    def __init__(self, *args, board=None, **kwargs):
        super().__init__(*args, **kwargs)
        if board and board.allowed_tags:
            tag_choices = [('', '-- 말머리 선택 --')]
            for tag in board.get_tags_list():
                tag_choices.append((tag, tag))
            self.fields['tag'].widget = forms.Select(choices=tag_choices, attrs={'class': 'form-select'})
        else:
            self.fields['tag'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': '말머리 (선택)'})

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ['trade_type', 'category', 'price', 'is_negotiable', 'condition', 'delivery', 'trade_location', 'status']
        widgets = {
            'trade_type':     forms.Select(attrs={'class': 'form-select'}),
            'category':       forms.Select(attrs={'class': 'form-select'}),
            'price':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0 (나눔이면 0 입력)'}),
            'is_negotiable':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'condition':      forms.Select(attrs={'class': 'form-select'}),
            'delivery':       forms.Select(attrs={'class': 'form-select'}),
            'trade_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '예: 단지 내 경비실 앞'}),
            'status':         forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'trade_type':     '거래 유형',
            'category':       '카테고리',
            'price':          '가격 (원)',
            'is_negotiable':  '가격 협의 가능',
            'condition':      '상품 상태',
            'delivery':       '거래 방법',
            'trade_location': '거래 희망 장소',
            'status':         '거래 상태',
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["start_time", "end_time", "location"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "장소"}),
        }
        labels = {
            "start_time": "시작 일시",
            "end_time": "종료 일시",
            "location": "장소",
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model = ActivityProof
        fields = ['activity', 'title', 'description', 'proof_image', 'duration_hours']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ActivityProofForm(forms.ModelForm):
    class Meta:
        model = ActivityProof
        fields = ['activity', 'title', 'description', 'proof_image', 'duration_hours']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '활동 제목을 입력하세요'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '활동 내용을 상세히 입력해주세요.'}),
            'proof_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.5', 'max': '24', 'step': '0.5'}),
        }
        labels = {
            'activity': '활동 종류',
            'title': '활동 제목',
            'description': '활동 내용',
            'proof_image': '인증 사진',
            'duration_hours': '활동 시간 (시간)',
        }


class PostImageForm(forms.ModelForm):
    class Meta:
        from hello_world.core.models import PostImage
        model = PostImage
        fields = ["image"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                
            })
        }
        labels = {"image": "이미지 첨부"}
