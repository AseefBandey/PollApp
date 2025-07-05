from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Poll, Choice
from .forms import PollAddForm, EditPollForm

def polls_list(request):
    all_polls = Poll.objects.all()
    paginator = Paginator(all_polls, 6)
    page = request.GET.get('page')
    polls = paginator.get_page(page)
    return render(request, 'polls/polls_list.html', {'polls': polls})

def polls_add(request):
    if request.method == 'POST':
        form = PollAddForm(request.POST)
        if form.is_valid():
            poll = form.save()
            choices = request.POST.get('choices', '').split('\n')
            choices = [choice.strip() for choice in choices if choice.strip()]
            
            if len(choices) < 2:
                poll.delete()
                messages.error(request, "You must provide at least 2 choices!")
                return render(request, 'polls/add_poll.html', {'form': form})
            
            # Check for duplicate choices
            if len(set(choices)) != len(choices):
                poll.delete()
                messages.error(request, "All choices must be unique!")
                return render(request, 'polls/add_poll.html', {'form': form})
            
            # Create choices
            for choice_text in choices:
                Choice.objects.create(poll=poll, choice_text=choice_text)
            
            messages.success(request, "Poll created successfully!")
            return redirect('polls:list')
    else:
        form = PollAddForm()
    return render(request, 'polls/add_poll.html', {'form': form})

def polls_edit(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if request.method == 'POST':
        form = EditPollForm(request.POST, instance=poll)
        if form.is_valid():
            form.save()
            choices = request.POST.get('choices', '').split('\n')
            choices = [choice.strip() for choice in choices if choice.strip()]
            
            if len(choices) < 2:
                messages.error(request, "You must provide at least 2 choices!")
                return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})
            
            # Check for duplicate choices
            if len(set(choices)) != len(choices):
                messages.error(request, "All choices must be unique!")
                return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})
            
            # Update choices
            poll.choice_set.all().delete()
            for choice_text in choices:
                Choice.objects.create(poll=poll, choice_text=choice_text)
            
            messages.success(request, "Poll updated successfully!")
            return redirect('polls:list')
    else:
        form = EditPollForm(instance=poll)
    return render(request, 'polls/poll_edit.html', {'form': form, 'poll': poll})

def polls_delete(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    poll.delete()
    messages.success(request, "Poll deleted successfully!")
    return redirect('polls:list')

def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if not poll.active:
        return render(request, 'polls/poll_result.html', {'poll': poll})
    return render(request, 'polls/poll_detail.html', {'poll': poll})

def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    if not poll.active:
        messages.error(request, "This poll has ended!")
        return redirect('polls:detail', poll_id)

    choice_id = request.POST.get('choice')
    if not choice_id:
        messages.error(request, "Please select an option to vote!")
        return redirect('polls:detail', poll_id)

    try:
        choice = Choice.objects.get(id=choice_id, poll=poll)
        choice.votes += 1
        choice.save()
        messages.success(request, "Your vote has been recorded!")
        return redirect('polls:results', poll_id)
    except Choice.DoesNotExist:
        messages.error(request, "Invalid choice selected!")
        return redirect('polls:detail', poll_id)

def poll_result(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    return render(request, 'polls/poll_result.html', {'poll': poll})
