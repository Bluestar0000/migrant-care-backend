from mongoengine import Document, StringField, DateTimeField, ListField
from datetime import datetime

class MedicalRecord(Document):
    user = StringField(required=True)
    disease = StringField()
    recurring_diseases = ListField(StringField())
    timestamp = DateTimeField(default=datetime.utcnow)

    def assign_schemes(self):
        # Placeholder logic for scheme matching
        eligible = []
        diseases = [d.lower().strip() for d in self.recurring_diseases]
        age = 35  # Replace with actual logic to get patient age

        from .mongo_models import Scheme  # Assuming you define Scheme model too
        schemes = Scheme.objects.filter(min_age__lte=age, max_age__gte=age)

        for scheme in schemes:
            if scheme.applicable_diseases:
                for d in scheme.applicable_diseases:
                    if d.lower().strip() in diseases:
                        eligible.append(scheme)
        return eligible