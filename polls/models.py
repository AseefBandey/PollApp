from django.db import models


class Poll(models.Model):
    question = models.CharField(max_length=100)
    pub_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

    def get_vote_count(self):
        return sum(choice.votes for choice in self.choice_set.all())

    def get_result_dict(self):
        total_votes = self.get_vote_count()
        choices = self.choice_set.all()
        result = []
        for choice in choices:
            percentage = (choice.votes / total_votes * 100) if total_votes > 0 else 0
            result.append({
                'text': choice.choice_text,
                'num_votes': choice.votes,
                'percentage': round(percentage, 1)
            })
        return result


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=100)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.poll.question[:25]} - {self.choice_text[:25]}"
