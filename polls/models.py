from django.db import models
from django.contrib.auth.models import User


class Poll(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='polls')
    question = models.CharField(max_length=255)
    pub_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.question

    @property
    def text(self):
        """Backward-compatibility alias for templates/code expecting .text"""
        return self.question

    def get_vote_count(self):
        """Returns the total number of votes cast for this poll."""
        return sum(choice.votes for choice in self.choice_set.all())

    def get_result_dict(self):
        """Returns structured results with percentages and UI alert classes for visual bars."""
        total_votes = self.get_vote_count()
        choices = self.choice_set.all()
        result = []
        alert_classes = ['primary', 'success', 'warning', 'info']

        for idx, choice in enumerate(choices):
            percentage = (choice.votes / total_votes * 100) if total_votes > 0 else 0
            result.append({
                'id': choice.id,
                'text': choice.choice_text,
                'num_votes': choice.votes,
                'percentage': round(percentage, 1),
                'alert_class': alert_classes[idx % len(alert_classes)]
            })
        return result

    def user_can_vote(self, user):
        """Checks whether the given user has already voted on this poll."""
        if not self.active:
            return False
        if user and user.is_authenticated:
            return not self.poll_votes.filter(user=user).exists()
        return True

    def end_poll(self):
        """Closes the poll to prevent further votes."""
        self.active = False
        self.save()


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choice_set')
    choice_text = models.CharField(max_length=255)
    votes = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.poll.question[:25]} - {self.choice_text[:25]}"

    def get_vote_count(self):
        """Backward-compatibility helper for templates."""
        return self.votes


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='poll_votes')
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name='choice_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='user_votes')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        voter = self.user.username if self.user else f"Guest ({self.ip_address or 'anon'})"
        return f"{voter} voted for '{self.choice.choice_text}' in '{self.poll.question}'"
