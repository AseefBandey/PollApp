import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from .models import Poll, Choice, Vote
from .forms import PollAddForm, EditPollForm


def get_client_ip(request):
    """Utility to extract client IP address across reverse proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def polls_list(request):
    """
    Lists all polls with search, status filtering, and pagination.
    """
    polls_query = Poll.objects.all().select_related('owner').prefetch_related('choice_set')

    # Search filtering
    search_query = request.GET.get('q', '').strip()
    if search_query:
        polls_query = polls_query.filter(
            Q(question__icontains=search_query) |
            Q(choice_set__choice_text__icontains=search_query)
        ).distinct()

    # Status filtering
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        polls_query = polls_query.filter(active=True)
    elif status_filter == 'closed':
        polls_query = polls_query.filter(active=False)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        polls_query = polls_query.order_by('pub_date')
    else:
        polls_query = polls_query.order_by('-pub_date')

    paginator = Paginator(polls_query, 6)
    page_number = request.GET.get('page')
    polls = paginator.get_page(page_number)

    context = {
        'polls': polls,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_polls_count': Poll.objects.count(),
    }
    return render(request, 'polls/polls_list.html', context)


@login_required
def polls_add(request):
    """
    Creates a new poll associated with the authenticated user.
    """
    if request.method == 'POST':
        form = PollAddForm(request.POST)
        if form.is_valid():
            # Extract choice options (from dynamic choice fields or choices textarea)
            raw_choices = request.POST.getlist('choice_items')
            if not raw_choices:
                choices_text = form.cleaned_data.get('choices', '')
                raw_choices = choices_text.split('\n')

            choices = [c.strip() for c in raw_choices if c.strip()]

            if len(choices) < 2:
                messages.error(request, "A poll requires at least 2 distinct choices.")
                return render(request, 'polls/add_poll.html', {'form': form})

            if len(set(choices)) != len(choices):
                messages.error(request, "All choices in a poll must be unique.")
                return render(request, 'polls/add_poll.html', {'form': form})

            with transaction.atomic():
                poll = form.save(commit=False)
                poll.owner = request.user
                poll.save()

                for choice_text in choices:
                    Choice.objects.create(poll=poll, choice_text=choice_text)

            messages.success(request, f"Poll '{poll.question}' was created successfully!")
            return redirect('polls:detail', poll_id=poll.id)
    else:
        form = PollAddForm()

    return render(request, 'polls/add_poll.html', {'form': form})


@login_required
def polls_edit(request, poll_id):
    """
    Edits a poll. Permitted only for the poll owner or staff.
    """
    poll = get_object_or_404(Poll, pk=poll_id)

    if poll.owner != request.user and not request.user.is_staff:
        messages.error(request, "Permission denied. You can only edit polls you created.")
        return redirect('polls:list')

    if request.method == 'POST':
        form = EditPollForm(request.POST, instance=poll)
        if form.is_valid():
            raw_choices = request.POST.getlist('choice_items')
            if not raw_choices:
                choices_text = form.cleaned_data.get('choices', '')
                raw_choices = choices_text.split('\n')

            choices = [c.strip() for c in raw_choices if c.strip()]

            if len(choices) < 2:
                messages.error(request, "A poll requires at least 2 distinct choices.")
                return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})

            if len(set(choices)) != len(choices):
                messages.error(request, "All choices must be unique.")
                return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})

            with transaction.atomic():
                updated_poll = form.save()
                # Update choices
                existing_choices = {c.choice_text: c for c in updated_poll.choice_set.all()}
                new_choice_texts = set(choices)

                # Delete choices no longer present
                for text, choice_obj in existing_choices.items():
                    if text not in new_choice_texts:
                        choice_obj.delete()

                # Add new choices
                for text in choices:
                    if text not in existing_choices:
                        Choice.objects.create(poll=updated_poll, choice_text=text)

            messages.success(request, "Poll updated successfully!")
            return redirect('polls:detail', poll_id=poll.id)
    else:
        form = EditPollForm(instance=poll)

    return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})


@login_required
def polls_delete(request, poll_id):
    """
    Deletes a poll. Permitted only for the poll owner or staff.
    """
    poll = get_object_or_404(Poll, pk=poll_id)

    if poll.owner != request.user and not request.user.is_staff:
        messages.error(request, "Permission denied. You can only delete polls you created.")
        return redirect('polls:list')

    question = poll.question
    poll.delete()
    messages.success(request, f"Poll '{question}' was deleted successfully.")
    return redirect('polls:list')


@login_required
def end_poll(request, poll_id):
    """
    Closes a poll immediately. Permitted only for the poll owner or staff.
    """
    poll = get_object_or_404(Poll, pk=poll_id)

    if poll.owner != request.user and not request.user.is_staff:
        messages.error(request, "Permission denied. You can only end polls you created.")
        return redirect('polls:detail', poll_id=poll.id)

    poll.end_poll()
    messages.success(request, f"Poll '{poll.question}' has been marked as closed.")
    return redirect('polls:results', poll_id=poll.id)


def poll_detail(request, poll_id):
    """
    Displays poll details and the voting interface.
    Redirects to results if poll has ended or user already voted.
    """
    poll = get_object_or_404(Poll.objects.prefetch_related('choice_set'), id=poll_id)

    user_voted = False
    if request.user.is_authenticated:
        user_voted = not poll.user_can_vote(request.user)
    elif request.session.get(f'voted_{poll.id}'):
        user_voted = True

    if not poll.active or user_voted:
        return render(request, 'polls/poll_result.html', {
            'poll': poll,
            'user_already_voted': user_voted,
            'chart_data_json': json.dumps(poll.get_result_dict())
        })

    return render(request, 'polls/poll_detail.html', {'poll': poll, 'user_already_voted': False})


def poll_vote(request, poll_id):
    """
    Records a vote atomically with duplicate check protection.
    """
    if request.method != 'POST':
        return redirect('polls:detail', poll_id=poll_id)

    poll = get_object_or_404(Poll, pk=poll_id)

    if not poll.active:
        messages.error(request, "This poll has ended and is no longer accepting votes.")
        return redirect('polls:results', poll_id=poll.id)

    # Check authenticated duplicate vote
    if request.user.is_authenticated and not poll.user_can_vote(request.user):
        messages.warning(request, "You have already cast your vote on this poll.")
        return redirect('polls:results', poll_id=poll.id)

    # Check guest session duplicate vote
    session_key = f'voted_{poll.id}'
    if not request.user.is_authenticated and request.session.get(session_key):
        messages.warning(request, "You have already cast a vote on this poll from this browser session.")
        return redirect('polls:results', poll_id=poll.id)

    choice_id = request.POST.get('choice')
    if not choice_id:
        messages.error(request, "Please select an option before submitting your vote.")
        return redirect('polls:detail', poll_id=poll.id)

    try:
        choice = Choice.objects.get(id=choice_id, poll=poll)
    except Choice.DoesNotExist:
        messages.error(request, "Invalid choice selected.")
        return redirect('polls:detail', poll_id=poll.id)

    client_ip = get_client_ip(request)

    # Atomic vote record & increment to prevent race conditions
    with transaction.atomic():
        Choice.objects.filter(id=choice.id).update(votes=F('votes') + 1)
        Vote.objects.create(
            poll=poll,
            choice=choice,
            user=request.user if request.user.is_authenticated else None,
            ip_address=client_ip
        )

    # Mark session
    request.session[session_key] = True

    messages.success(request, f"Your vote for '{choice.choice_text}' has been recorded!")
    return redirect('polls:results', poll_id=poll.id)


def poll_result(request, poll_id):
    """
    Displays results, percentages, and interactive Chart.js visualization.
    """
    poll = get_object_or_404(Poll.objects.prefetch_related('choice_set'), pk=poll_id)
    result_dict = poll.get_result_dict()

    user_voted = False
    if request.user.is_authenticated:
        user_voted = not poll.user_can_vote(request.user)
    elif request.session.get(f'voted_{poll.id}'):
        user_voted = True

    context = {
        'poll': poll,
        'user_already_voted': user_voted,
        'chart_data_json': json.dumps(result_dict),
    }
    return render(request, 'polls/poll_result.html', context)


def poll_result_api(request, poll_id):
    """
    JSON endpoint for live chart polling / real-time updates.
    """
    poll = get_object_or_404(Poll, pk=poll_id)
    return JsonResponse({
        'id': poll.id,
        'question': poll.question,
        'active': poll.active,
        'total_votes': poll.get_vote_count(),
        'results': poll.get_result_dict(),
    })
