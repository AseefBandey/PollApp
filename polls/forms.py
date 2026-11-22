from django import forms
from .models import Poll, Choice


class PollAddForm(forms.ModelForm):
    choices = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Enter choices, one per line:\nOption 1\nOption 2\nOption 3',
            'class': 'w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors'
        }),
        required=False,
        help_text="Provide at least 2 unique choices (one per line)."
    )

    class Meta:
        model = Poll
        fields = ['question']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors',
                'placeholder': 'Enter your poll question (e.g. Which web framework do you prefer?)'
            })
        }

    def clean_question(self):
        question = self.cleaned_data.get('question', '').strip()
        if len(question) < 5:
            raise forms.ValidationError("Poll question must be at least 5 characters long.")
        return question


class EditPollForm(forms.ModelForm):
    choices = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors'
        }),
        required=False,
        help_text="Edit choices (one per line). Warning: modifying choices resets choice vote counts."
    )

    class Meta:
        model = Poll
        fields = ['question', 'active']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary rounded border-gray-700 bg-gray-800 focus:ring-primary'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_choices = self.instance.choice_set.all()
            self.initial['choices'] = '\n'.join(c.choice_text for c in current_choices)


class ChoiceAddForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text']
        widgets = {
            'choice_text': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-50 transition-colors',
                'placeholder': 'Enter choice option'
            })
        }
