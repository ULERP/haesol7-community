from django import forms
from .models import Post, Trade, Event, ActivityProof

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ['item_name', 'status', 'price']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'start_date', 'end_date', 'location']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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