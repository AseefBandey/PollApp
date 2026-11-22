from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from polls.models import Poll, Choice, Vote


class Command(BaseCommand):
    help = "Populates the database with realistic sample polls, choices, and votes for demonstration."

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for PollMe...")

        # Create demo superuser
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@pollme.io", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo admin user: admin / admin123"))

        # Create demo creator user
        demo_user, created = User.objects.get_or_create(
            username="demouser",
            defaults={"email": "demo@pollme.io"}
        )
        if created:
            demo_user.set_password("demo12345")
            demo_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demouser / demo12345"))

        sample_polls = [
            {
                "question": "Which backend framework do you prefer for scalable web APIs?",
                "owner": demo_user,
                "choices": [
                    ("Django / Django REST Framework", 48),
                    ("FastAPI (Python)", 37),
                    ("Go (Gin / Fiber)", 29),
                    ("Node.js (NestJS / Express)", 21),
                    ("Rust (Actix-web / Axum)", 14),
                ]
            },
            {
                "question": "What is your primary cloud platform for production workloads?",
                "owner": admin_user,
                "choices": [
                    ("Amazon Web Services (AWS)", 65),
                    ("Google Cloud Platform (GCP)", 42),
                    ("Microsoft Azure", 28),
                    ("Self-hosted / Hetzner / DigitalOcean", 19),
                ]
            },
            {
                "question": "Which database architecture best fits high-concurrency event telemetry?",
                "owner": demo_user,
                "choices": [
                    ("PostgreSQL with TimescaleDB", 53),
                    ("ClickHouse OLAP Engine", 39),
                    ("Redis Streams + Worker", 31),
                    ("MongoDB Atlas", 12),
                ]
            },
            {
                "question": "Tabs vs Spaces: The eternal engineering preference",
                "owner": admin_user,
                "choices": [
                    ("Spaces (2 or 4)", 58),
                    ("Tabs (configured to 2/4 in editor)", 35),
                    ("I let the code formatter (Prettier / Black) decide", 82),
                ]
            }
        ]

        for p_data in sample_polls:
            poll, p_created = Poll.objects.get_or_create(
                question=p_data["question"],
                defaults={"owner": p_data["owner"], "active": True}
            )
            if p_created:
                for text, votes in p_data["choices"]:
                    choice = Choice.objects.create(poll=poll, choice_text=text, votes=votes)
                    # Seed a sample Vote row
                    Vote.objects.create(poll=poll, choice=choice, user=p_data["owner"])
                self.stdout.write(self.style.SUCCESS(f"Seeded poll: '{poll.question}'"))

        self.stdout.write(self.style.SUCCESS("Seeding complete! Database is populated and ready for demos."))
