from django import forms
from .models import Poll, Choice


class PollAddForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter your poll question (minimum 10 characters)'
            })
        }


class EditPollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter your poll question (minimum 10 characters)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            choices = self.instance.choice_set.all()
            self.initial['choices'] = '\n'.join(choice.choice_text for choice in choices)


class ChoiceAddForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', ]
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control', })
        }
