from django.shortcuts import render
from polls.models import Poll, Vote


def home(request):
    """
    Landing page showcasing platform statistics and featured polls.
    """
    total_polls = Poll.objects.count()
    active_polls = Poll.objects.filter(active=True).count()
    total_votes = Vote.objects.count() + sum(c.votes for c in Poll.objects.all().prefetch_related('choice_set') for c in c.choice_set.all()) // 2
    # Ensure reasonable total_votes count if no votes in Vote table yet
    if total_votes == 0:
        total_votes = sum(c.votes for p in Poll.objects.all() for c in p.choice_set.all())

    recent_polls = Poll.objects.filter(active=True).prefetch_related('choice_set')[:3]

    context = {
        'total_polls': total_polls,
        'active_polls': active_polls,
        'total_votes': total_votes,
        'recent_polls': recent_polls,
    }
    return render(request, 'home.html', context)
