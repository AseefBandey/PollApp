from rest_framework import serializers, status, views, permissions
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Poll, Choice, Vote


class ChoiceSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'votes', 'percentage']

    def get_percentage(self, obj):
        total = obj.poll.get_vote_count()
        return round((obj.votes / total * 100), 1) if total > 0 else 0.0


class PollSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    choices = ChoiceSerializer(source='choice_set', many=True, read_only=True)
    total_votes = serializers.IntegerField(source='get_vote_count', read_only=True)

    class Meta:
        model = Poll
        fields = ['id', 'question', 'pub_date', 'active', 'owner_username', 'total_votes', 'choices']
        read_only_fields = ['pub_date', 'owner_username', 'total_votes', 'choices']


class PollCreateSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        min_length=2,
        help_text="List of at least 2 distinct choice strings."
    )

    class Meta:
        model = Poll
        fields = ['id', 'question', 'choices']

    def validate_choices(self, choices):
        cleaned = [c.strip() for c in choices if c.strip()]
        if len(cleaned) < 2:
            raise serializers.ValidationError("At least 2 non-empty choices are required.")
        if len(set(cleaned)) != len(cleaned):
            raise serializers.ValidationError("All choices must be distinct.")
        return cleaned

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        user = self.context['request'].user
        with transaction.atomic():
            poll = Poll.objects.create(
                owner=user if user.is_authenticated else None,
                **validated_data
            )
            for text in choices_data:
                Choice.objects.create(poll=poll, choice_text=text)
        return poll


class VoteSubmitSerializer(serializers.Serializer):
    choice_id = serializers.IntegerField(help_text="ID of the choice to vote for.")


class PollListCreateAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="List all polls",
        description="Returns a paginated list of all active and closed polls.",
        responses={200: PollSerializer(many=True)}
    )
    def get(self, request):
        polls = Poll.objects.all().select_related('owner').prefetch_related('choice_set')
        serializer = PollSerializer(polls, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create a new poll",
        description="Creates a poll with a question and choices array. Authenticated users are assigned as owner.",
        request=PollCreateSerializer,
        responses={201: PollSerializer}
    )
    def post(self, request):
        serializer = PollCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            poll = serializer.save()
            return Response(PollSerializer(poll).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PollDetailAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Retrieve poll details",
        description="Retrieves a single poll with all choices, vote tallies, and percentage distributions.",
        responses={200: PollSerializer}
    )
    def get(self, request, pk):
        try:
            poll = Poll.objects.select_related('owner').prefetch_related('choice_set').get(pk=pk)
        except Poll.DoesNotExist:
            return Response({'detail': 'Poll not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PollSerializer(poll)
        return Response(serializer.data)

    @extend_schema(
        summary="Delete a poll",
        description="Deletes a poll. Allowed only for poll owner or staff.",
        responses={204: OpenApiResponse(description="Poll deleted successfully")}
    )
    def delete(self, request, pk):
        try:
            poll = Poll.objects.get(pk=pk)
        except Poll.DoesNotExist:
            return Response({'detail': 'Poll not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        if poll.owner != request.user and not request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        poll.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PollVoteAPI(views.APIView):
    @extend_schema(
        summary="Submit a vote",
        description="Casts a vote for a specific choice. Enforces duplicate voting safeguards.",
        request=VoteSubmitSerializer,
        responses={
            200: OpenApiResponse(description="Vote recorded successfully"),
            400: OpenApiResponse(description="Poll inactive or already voted")
        }
    )
    def post(self, request, pk):
        try:
            poll = Poll.objects.get(pk=pk)
        except Poll.DoesNotExist:
            return Response({'detail': 'Poll not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not poll.active:
            return Response({'detail': 'This poll has ended.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check duplicate
        if request.user.is_authenticated and not poll.user_can_vote(request.user):
            return Response({'detail': 'User has already voted in this poll.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VoteSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        choice_id = serializer.validated_data['choice_id']
        try:
            choice = Choice.objects.get(id=choice_id, poll=poll)
        except Choice.DoesNotExist:
            return Response({'detail': 'Invalid choice_id for this poll.'}, status=status.HTTP_400_BAD_REQUEST)

        # Atomic increment & Vote creation
        with transaction.atomic():
            Choice.objects.filter(id=choice.id).update(votes=F('votes') + 1)
            Vote.objects.create(
                poll=poll,
                choice=choice,
                user=request.user if request.user.is_authenticated else None,
            )

        return Response({
            'detail': 'Vote recorded successfully.',
            'choice_voted': choice.choice_text,
            'poll_results': poll.get_result_dict()
        }, status=status.HTTP_200_OK)


class PollResultAPI(views.APIView):
    @extend_schema(
        summary="Get live poll results",
        description="Returns real-time aggregated vote tallies and percentages for visualization.",
        responses={200: OpenApiResponse(description="Results dictionary")}
    )
    def get(self, request, pk):
        try:
            poll = Poll.objects.prefetch_related('choice_set').get(pk=pk)
        except Poll.DoesNotExist:
            return Response({'detail': 'Poll not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'poll_id': poll.id,
            'question': poll.question,
            'active': poll.active,
            'total_votes': poll.get_vote_count(),
            'results': poll.get_result_dict()
        })
