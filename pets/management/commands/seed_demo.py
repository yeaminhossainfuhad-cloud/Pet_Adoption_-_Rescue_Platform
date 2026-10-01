from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pets.models import Pet

PETS = [
    ("Max", "Dog", "Golden Retriever", 2, "Male", "Dhaka", "Max is friendly and playful. He loves fetch and gets along with children."),
    ("Luna", "Cat", "Persian", 1, "Female", "Chattogram", "Luna is a calm lap cat who enjoys sunny windowsills."),
    ("Coco", "Rabbit", "Holland Lop", 0, "Female", "Dhaka", "Coco is a curious young rabbit who loves fresh greens."),
    ("Rocky", "Dog", "German Shepherd", 4, "Male", "Sylhet", "Rocky is loyal and well trained, and needs space to run."),
    ("Mimi", "Cat", "Domestic Shorthair", 3, "Female", "Dhaka", "Mimi was found near a market and is now fully vaccinated."),
    ("Kiwi", "Bird", "Cockatiel", 2, "Male", "Khulna", "Kiwi whistles every morning and enjoys company."),
    ("Bruno", "Dog", "Labrador", 5, "Male", "Rajshahi", "Bruno is gentle, calm and great with other dogs."),
    ("Snowy", "Rabbit", "Mini Rex", 1, "Male", "Dhaka", "Snowy is shy at first but very affectionate once settled."),
    ("Tiger", "Cat", "Tabby", 2, "Male", "Chattogram", "Tiger is energetic and loves to climb."),
    ("Daisy", "Dog", "Beagle", 3, "Female", "Dhaka", "Daisy has a great nose and an even better temper."),
    ("Pip", "Bird", "Budgerigar", 1, "Female", "Dhaka", "Pip is social and learns new sounds quickly."),
    ("Oreo", "Other", "Guinea Pig", 1, "Male", "Sylhet", "Oreo is a gentle guinea pig who squeaks for snacks."),
]


class Command(BaseCommand):
    help = "Create demo pets and a demo user (no images; add photos in the admin)."

    def handle(self, *args, **options):
        created = 0
        for name, kind, breed, age, gender, location, description in PETS:
            _, was_created = Pet.objects.get_or_create(
                name=name, animal_type=kind,
                defaults=dict(breed=breed, age=age, gender=gender,
                              location=location, description=description),
            )
            created += was_created
        user, user_created = User.objects.get_or_create(
            username="rahim", defaults={"email": "rahim@example.com"}
        )
        if user_created:
            user.set_password("demo-pass-123")
            user.save()
        self.stdout.write(self.style.SUCCESS(
            f"{created} pets created. Demo user: rahim / demo-pass-123"
        ))
