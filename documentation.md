# Django Poll Application Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Authentication System](#authentication-system)
5. [Poll Management System](#poll-management-system)
6. [Frontend Templates](#frontend-templates)
7. [Database Models](#database-models)
8. [URL Configuration](#url-configuration)
9. [Forms](#forms)
10. [Static Files](#static-files)

## 1. Project Overview

This Django Poll Application is a web-based polling system that allows users to:
- Create and manage polls
- Vote on active polls
- View poll results
- Manage their own polls
- Register and authenticate users

### Technical Stack
- Backend: Django (Python web framework)
- Frontend: HTML5, CSS (with modern styling)
- Database: SQLite
- Authentication: Django's built-in auth system

## 2. Project Structure

```
Django-Poll-App/
├── pollme/                 # Main project configuration
├── accounts/              # User authentication app
├── polls/                 # Poll management app
├── static/               # Static files (CSS, JS, images)
└── templates/            # Base templates
```

## 3. Core Components

### Main Project Configuration (pollme/)

#### settings.py
```python
# Key configurations:
- Database settings
- Installed applications
- Middleware configuration
- Template configuration
- Static files settings
- Authentication settings
```

#### urls.py
```python
# Main URL routing:
- Root URL patterns
- App-specific URL includes
- Static file serving
```

## 4. Authentication System (accounts/)

### Views (accounts/views.py)

#### login_user()
```python
def login_user(request):
    """
    Handles user login with the following features:
    - Validates user credentials
    - Creates user session
    - Redirects to next URL or home
    - Displays success/error messages
    """
```

#### logout_user()
```python
def logout_user(request):
    """
    Handles user logout:
    - Destroys user session
    - Redirects to home
    - Shows success message
    """
```

#### create_user()
```python
def create_user(request):
    """
    Handles new user registration:
    - Validates user input
    - Creates new user account
    - Handles form errors
    - Shows success/error messages
    """
```

### Forms (accounts/forms.py)

#### UserRegistrationForm
```python
class UserRegistrationForm(UserCreationForm):
    """
    Custom registration form with:
    - Email validation
    - Username validation
    - Password requirements
    - Custom error messages
    """
```

## 5. Poll Management System (polls/)

### Models (polls/models.py)

#### Poll Model
```python
class Poll(models.Model):
    """
    Represents a poll with:
    - Question text
    - Creation date
    - Owner (User)
    - Active status
    """
```

#### Choice Model
```python
class Choice(models.Model):
    """
    Represents a poll choice with:
    - Choice text
    - Vote count
    - Related poll
    """
```

#### Vote Model
```python
class Vote(models.Model):
    """
    Tracks user votes with:
    - User reference
    - Poll reference
    - Choice reference
    - Timestamp
    """
```

### Views (polls/views.py)

#### polls_list()
```python
@login_required()
def polls_list(request):
    """
    Displays all polls with:
    - Pagination
    - 6 polls per page
    - Accessible to logged-in users
    """
```

#### polls_add()
```python
@login_required()
def polls_add(request):
    """
    Handles poll creation:
    - Permission checking
    - Form validation
    - Choice creation
    - Success/error messages
    """
```

#### polls_edit()
```python
@login_required
def polls_edit(request, poll_id):
    """
    Handles poll editing:
    - Owner verification
    - Updates poll question
    - Updates choices
    - Handles validation
    """
```

#### poll_vote()
```python
@login_required
def poll_vote(request, poll_id):
    """
    Manages voting process:
    - Checks poll status
    - Prevents duplicate voting
    - Records votes
    - Shows results
    """
```

## 6. Frontend Templates

### Base Template (templates/base.html)
```html
<!-- Base template features:
- Common layout
- Navigation bar
- Message display
- Content blocks
- Static file inclusion
-->
```

### Poll Templates (polls/templates/)

#### polls_list.html
```html
<!-- Lists all polls with:
- Poll questions
- Creation date
- Owner info
- Vote counts
- Action buttons
-->
```

#### poll_detail.html
```html
<!-- Shows poll details:
- Poll question
- Voting form
- Choice options
- Submit button
-->
```

#### poll_result.html
```html
<!-- Displays poll results:
- Vote counts
- Percentages
- Visual representation
- Back button
-->
```

## 7. Database Models

### User Model (Extended Django User)
- Username
- Email
- Password
- Permissions

### Poll Model
- question (CharField)
- pub_date (DateTimeField)
- owner (ForeignKey to User)
- active (BooleanField)

### Choice Model
- poll (ForeignKey to Poll)
- choice_text (CharField)
- votes (IntegerField)

### Vote Model
- user (ForeignKey to User)
- poll (ForeignKey to Poll)
- choice (ForeignKey to Choice)
- timestamp (DateTimeField)

## 8. URL Configuration

### Main URLs (pollme/urls.py)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('polls/', include('polls.urls')),
    path('', views.home, name='home'),
]
```

### Polls URLs (polls/urls.py)
```python
urlpatterns = [
    path('list/', views.polls_list, name='list'),
    path('add/', views.polls_add, name='add'),
    path('edit/<int:poll_id>/', views.polls_edit, name='edit'),
    path('delete/<int:poll_id>/', views.polls_delete, name='delete'),
    path('end/<int:poll_id>/', views.end_poll, name='end'),
    path('vote/<int:poll_id>/', views.poll_vote, name='vote'),
]
```

## 9. Forms

### Poll Forms (polls/forms.py)

#### PollAddForm
```python
class PollAddForm(forms.ModelForm):
    """
    Form for creating new polls:
    - Question field
    - Dynamic choice fields
    - Validation logic
    """
```

#### EditPollForm
```python
class EditPollForm(forms.ModelForm):
    """
    Form for editing existing polls:
    - Updates question
    - Manages choices
    - Validation rules
    """
```

## 10. Static Files

### CSS (static/css/)
- Modern styling
- Responsive design
- Custom components
- Alert styles

### Images (static/img/)
- Background images
- Icons
- UI elements

## Security Features

1. Authentication Protection
- Login required decorators
- Session management
- Password hashing

2. Form Security
- CSRF protection
- Input validation
- XSS prevention

3. Access Control
- Owner verification
- Permission checking
- Vote validation

## Best Practices Implemented

1. Code Organization
- Modular structure
- Clear separation of concerns
- DRY principles

2. User Experience
- Clear messages
- Intuitive navigation
- Responsive design

3. Error Handling
- Form validation
- User feedback
- Exception handling

## Future Enhancements

1. Features to Add
- Poll categories
- Advanced analytics
- Social sharing
- Image support

2. Technical Improvements
- Caching system
- API endpoints
- Test coverage
- Performance optimization 