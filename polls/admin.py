from django.contrib import admin
from .models import Poll, Choice


class ChoiceInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = Choice
    extra = 2

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['question', 'pub_date', 'active']
    search_fields = ['question']
    list_filter = ['active', 'pub_date']
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'poll', 'votes']
    search_fields = ['choice_text', 'poll__question']
    list_filter = ['poll']
