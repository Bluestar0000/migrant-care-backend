from django.core.management.base import BaseCommand
from HealthBridge.models import Profile, MedicalRecord
import random
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Generate test data'

    def handle(self, *args, **kwargs):
        for _ in range(10):
            profile = Profile.objects.create(
                name=fake.name(),
                age=random.randint(18, 70),
                gender=random.choice(['Male', 'Female']),
                location=fake.city(),
                language=random.choice(['Hindi', 'Malayalam']),
                blood_group=random.choice(['A+', 'B+', 'O-', 'AB+']),
                migrant_id=f"AWZ{random.randint(100000,999999)}"
            )
            MedicalRecord.objects.create(
                title="Test Treatment",
                description="Simulated fever and fatigue",
                patient=profile
            )
        self.stdout.write(self.style.SUCCESS('Test data created successfully'))