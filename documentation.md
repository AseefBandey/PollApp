# PollMe Technical Documentation

## 1. Project Overview
PollMe is a production-grade web application and RESTful API for conducting online surveys, opinion polling, and real-time vote analytics.

### Technical Stack
- **Backend Framework**: Django 5 / Python 3.11+
- **API Framework**: Django REST Framework (DRF) + `drf-spectacular` (OpenAPI 3.0)
- **Frontend Architecture**: Server-rendered Django Templates styled with Tailwind CSS & FontAwesome
- **Data Visualizations**: Chart.js (interactive bar & doughnut visualizations)
- **Database**: SQLite (default dev) / PostgreSQL (production container ready)
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD

---

## 2. Directory Structure
```
PollApp/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── pollme/                  # Core configuration
│   ├── settings.py
│   ├── urls.py
│   ├── views.py             # Landing page metrics
│   └── wsgi.py
├── accounts/                # Authentication & User Profiles
│   ├── forms.py
│   ├── urls.py
│   └── views.py             # Login, register, logout, dashboard
├── polls/                   # Polling Engine & API
│   ├── models.py            # Poll, Choice, Vote
│   ├── views.py             # Voting, results, poll lifecycle
│   ├── api.py               # REST API views & serializers
│   ├── forms.py
│   ├── urls.py
│   ├── tests.py             # Automated unit & integration tests
│   └── management/
│       └── commands/
│           └── seed_data.py # Demo database population
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── includes/
│   │   └── navbar.html
│   └── accounts/
│       ├── login.html
│       ├── register.html
│       └── profile.html
└── static/
```

---

## 3. Data Models

### `Poll`
- `owner`: Foreign key to `auth.User` (nullable for guest-created polls).
- `question`: CharField (max 255 chars).
- `pub_date`: DateTimeField (auto created).
- `active`: Boolean flag indicating if poll accepts votes.
- Helper methods:
  - `get_vote_count()`: Total votes cast across all choices.
  - `get_result_dict()`: List of choice dictionaries with vote count, calculated percentages, and visual alert classes.
  - `user_can_vote(user)`: Returns boolean indicating if a user can vote.
  - `end_poll()`: Closes the poll to new votes.

### `Choice`
- `poll`: Foreign key to `Poll`.
- `choice_text`: CharField (max 255 chars).
- `votes`: Denormalized integer count updated via atomic database increments.

### `Vote`
- `poll`: Foreign key to `Poll`.
- `choice`: Foreign key to `Choice`.
- `user`: Foreign key to `auth.User` (nullable for anonymous votes).
- `ip_address`: Generic IP address recorded at vote time.
- `timestamp`: DateTimeField of submission.

---

## 4. Concurrency & Security Architecture

1. **Race Condition Prevention**:
   ```python
   with transaction.atomic():
       Choice.objects.filter(id=choice.id).update(votes=F('votes') + 1)
       Vote.objects.create(poll=poll, choice=choice, user=request.user if request.user.is_authenticated else None)
   ```
2. **Access Control**:
   - Only the poll owner (or staff/superuser) can edit, delete, or end a poll.
   - Non-authenticated users attempting to create polls are redirected to the login page.
3. **Duplicate Voting Prevention**:
   - Authenticated: `poll.user_can_vote(request.user)` validates against existing `Vote` records.
   - Anonymous / Guest: Encrypted session token (`voted_<poll_id>`) stored in client cookie session.

---

## 5. REST API Specifications

Accessible via Swagger at `/api/docs/` and Redoc at `/api/redoc/`.

- `GET /polls/api/polls/`: Retrieve list of all polls.
- `POST /polls/api/polls/`: Create a poll (`{ "question": "...", "choices": ["A", "B"] }`).
- `GET /polls/api/polls/{id}/`: Retrieve detailed poll representation.
- `POST /polls/api/polls/{id}/vote/`: Cast a vote (`{ "choice_id": 1 }`).
- `GET /polls/api/polls/{id}/results/`: Retrieve calculated percentages.

---

## 6. Seed Data & Local Setup
Run `python manage.py seed_data` to populate sample polls and default users:
- `admin` / `admin123`
- `demouser` / `demo12345`
