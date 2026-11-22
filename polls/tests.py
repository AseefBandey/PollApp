from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Poll, Choice, Vote


class PollModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.poll = Poll.objects.create(question="Favorite Language?", owner=self.user)
        self.choice1 = Choice.objects.create(poll=self.poll, choice_text="Python", votes=3)
        self.choice2 = Choice.objects.create(poll=self.poll, choice_text="Go", votes=1)

    def test_poll_string_and_properties(self):
        self.assertEqual(str(self.poll), "Favorite Language?")
        self.assertEqual(self.poll.text, "Favorite Language?")
        self.assertEqual(self.poll.get_vote_count(), 4)

    def test_result_dictionary(self):
        results = self.poll.get_result_dict()
        self.assertEqual(len(results), 2)
        # 3 out of 4 is 75.0%
        self.assertEqual(results[0]['percentage'], 75.0)
        self.assertEqual(results[0]['num_votes'], 3)
        # 1 out of 4 is 25.0%
        self.assertEqual(results[1]['percentage'], 25.0)
        self.assertEqual(results[1]['num_votes'], 1)

    def test_user_can_vote(self):
        self.assertTrue(self.poll.user_can_vote(self.user))
        # Record a vote
        Vote.objects.create(poll=self.poll, choice=self.choice1, user=self.user)
        self.assertFalse(self.poll.user_can_vote(self.user))

        # Check ending poll prevents voting
        other_user = User.objects.create_user(username='other', password='password123')
        self.poll.end_poll()
        self.assertFalse(self.poll.user_can_vote(other_user))


class PollViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='voter', password='password123')
        self.poll = Poll.objects.create(question="Tabs vs Spaces?", owner=self.user)
        self.choice1 = Choice.objects.create(poll=self.poll, choice_text="Tabs")
        self.choice2 = Choice.objects.create(poll=self.poll, choice_text="Spaces")

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PollMe")

    def test_polls_list(self):
        response = self.client.get(reverse('polls:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tabs vs Spaces?")

    def test_poll_detail(self):
        response = self.client.get(reverse('polls:detail', args=[self.poll.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tabs")
        self.assertContains(response, "Spaces")

    def test_poll_voting_authenticated(self):
        self.client.login(username='voter', password='password123')
        response = self.client.post(reverse('polls:vote', args=[self.poll.id]), {'choice': self.choice1.id})
        self.assertRedirects(response, reverse('polls:results', args=[self.poll.id]))

        self.choice1.refresh_from_db()
        self.assertEqual(self.choice1.votes, 1)
        self.assertTrue(Vote.objects.filter(poll=self.poll, user=self.user).exists())

        # Attempt duplicate vote should be blocked
        dup_response = self.client.post(reverse('polls:vote', args=[self.poll.id]), {'choice': self.choice2.id})
        self.assertRedirects(dup_response, reverse('polls:results', args=[self.poll.id]))
        self.choice2.refresh_from_db()
        self.assertEqual(self.choice2.votes, 0)

    def test_create_poll_view(self):
        self.client.login(username='voter', password='password123')
        response = self.client.post(reverse('polls:add'), {
            'question': 'Which database do you prefer?',
            'choice_items': ['PostgreSQL', 'Redis', 'SQLite']
        })
        new_poll = Poll.objects.filter(question='Which database do you prefer?').first()
        self.assertIsNotNone(new_poll)
        self.assertEqual(new_poll.choice_set.count(), 3)
        self.assertEqual(new_poll.owner, self.user)

    def test_end_poll_by_owner(self):
        self.client.login(username='voter', password='password123')
        response = self.client.get(reverse('polls:end_poll', args=[self.poll.id]))
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.active)


class AccountsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_and_login(self):
        # Register user
        reg_response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'safe_password_123',
            'confirm_password': 'safe_password_123'
        })
        self.assertRedirects(reg_response, reverse('accounts:login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Login user
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'newuser',
            'password': 'safe_password_123'
        })
        self.assertRedirects(login_response, reverse('polls:list'))

        # Logout user
        logout_response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(logout_response, reverse('home'))


class PollAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='apiuser', password='password123')
        self.poll = Poll.objects.create(question="REST or GraphQL?", owner=self.user)
        self.choice1 = Choice.objects.create(poll=self.poll, choice_text="REST")
        self.choice2 = Choice.objects.create(poll=self.poll, choice_text="GraphQL")

    def test_api_list_polls(self):
        response = self.client.get(reverse('polls:api_poll_list_create'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_api_vote(self):
        self.client.login(username='apiuser', password='password123')
        response = self.client.post(
            reverse('polls:api_poll_vote', args=[self.poll.id]),
            {'choice_id': self.choice1.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.choice1.refresh_from_db()
        self.assertEqual(self.choice1.votes, 1)

    def test_api_results(self):
        response = self.client.get(reverse('polls:api_poll_results', args=[self.poll.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['question'], "REST or GraphQL?")
