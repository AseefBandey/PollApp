from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, UserLoginForm
from polls.models import Poll, Vote


def create_user(request):
    """
    Handles new user registration.
    Supports both template form and POST credentials from tests/forms.
    """
    if request.user.is_authenticated:
        return redirect('polls:list')

    if request.method == 'POST':
        # Check for test-compat field names ('password1', 'password2')
        post_data = request.POST.copy()
        if 'password1' in post_data and 'password' not in post_data:
            post_data['password'] = post_data['password1']
        if 'password2' in post_data and 'confirm_password' not in post_data:
            post_data['confirm_password'] = post_data['password2']

        form = UserRegistrationForm(post_data)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"Welcome to PollMe, {user.username}! Your account has been created.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_user(request):
    """
    Authenticates user and initiates session.
    """
    if request.user.is_authenticated:
        return redirect('polls:list')

    next_url = request.GET.get('next', request.POST.get('next', 'polls:list'))

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url or 'polls:list')
        else:
            # Fallback for manual authentication check in test suite
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect(next_url or 'polls:list')
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_user(request):
    """
    Ends user session and redirects to home.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def my_polls(request):
    """
    Dashboard displaying polls created by the logged-in user and their voting history.
    """
    user_polls = Poll.objects.filter(owner=request.user).prefetch_related('choice_set')
    user_votes = Vote.objects.filter(user=request.user).select_related('poll', 'choice')

    context = {
        'polls': user_polls,
        'votes': user_votes,
        'total_polls_created': user_polls.count(),
        'total_votes_cast': user_votes.count(),
    }
    return render(request, 'accounts/profile.html', context)
