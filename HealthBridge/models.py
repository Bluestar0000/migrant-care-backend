from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

# -------------------------------
# Profile Model
# -------------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    migrant_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, default="Unnamed Migrant")
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[("M", "Male"), ("F", "Female"), ("O", "Other")])
    location = models.CharField(max_length=100)
    language = models.CharField(max_length=50, default="Malayalam")
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ("A+", "A+"), ("A-", "A-"),
            ("B+", "B+"), ("B-", "B-"),
            ("O+", "O+"), ("O-", "O-"),
            ("AB+", "AB+"), ("AB-", "AB-")
        ],
        null=True,
        blank=True
    )
    migrant_only = models.BooleanField(default=True)
    awaz_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()

        qr_data = self.awaz_id if self.awaz_id else str(self.qr_code_uuid)
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        filename = f"{self.user.username}_qr.png"
        self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.migrant_id})"

# -------------------------------
# Scheme Model
# -------------------------------
class Scheme(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_age = models.IntegerField()
    max_age = models.IntegerField()
    applicable_diseases = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# -------------------------------
# DoctorProfile Model
# -------------------------------
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital_id = models.CharField(max_length=50, unique=True)
    hospital_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} ({self.hospital_name})"

# -------------------------------
# MedicalRecord Model
# -------------------------------
class MedicalRecord(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='medical_records')
    recurring_diseases = models.TextField(blank=True, null=True)
    current_symptoms = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='treated_records')
    treated_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    eligible_schemes = models.ManyToManyField(Scheme, blank=True, related_name='beneficiaries')
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MedicalRecord of {self.patient.user.username} ({self.qr_code_uuid})"

    def assign_schemes(self):
        age = self.patient.age
        diseases = [d.strip().lower() for d in (self.recurring_diseases or "").split(",")]
        eligible = Scheme.objects.filter(min_age__lte=age, max_age__gte=age)
        final_schemes = []

        for scheme in eligible:
            if scheme.applicable_diseases:
                scheme_diseases = [d.strip().lower() for d in scheme.applicable_diseases.split(",")]
                if any(d in diseases for d in scheme_diseases):
                    final_schemes.append(scheme)
            else:
                final_schemes.append(scheme)

        self.eligible_schemes.set(final_schemes)
        self.save()

# -------------------------------
# Recommendation Model
# -------------------------------
class Recommendation(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recommendations')
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_by_patient = models.BooleanField(default=False)

    def __str__(self):
        return f"Recommendation for {self.patient.user.username}: {self.title}"

    @classmethod
    def generate_ai_recommendations(cls, medical_record):
        recommendations = []
        diseases = [d.strip().lower() for d in (medical_record.recurring_diseases or "").split(",")]
        symptoms = [s.strip().lower() for s in (medical_record.current_symptoms or "").split(",")]

        if "diabetes" in diseases:
            recommendations.append({
                "title": "Diabetes Management",
                "description": "Maintain blood sugar levels, follow diet plan, and get regular checkups."
            })

        if "hypertension" in diseases:
            recommendations.append({
                "title": "Hypertension Care",
                "description": "Monitor blood pressure daily and reduce salt intake."
            })

        if "fever" in symptoms:
            recommendations.append({
                "title": "Fever Alert",
                "description": "Take rest, drink fluids, and consult a doctor if persistent."
            })

        if "cough" in symptoms:
            recommendations.append({
                "title": "Respiratory Care",
                "description": "Persistent cough may indicate respiratory issues. Consider a checkup."
            })

        if "fatigue" in symptoms:
            recommendations.append({
                "title": "Energy & Nutrition",
                "description": "Fatigue can be linked to poor nutrition or stress. Explore wellness programs."
            })

        if medical_record.patient.age >= 50:
            recommendations.append({
                "title": "Senior Health Checkup",
                "description": "Annual full body checkup recommended for people above 50."
            })

        rec_objects = []
        for rec in recommendations:
            rec_obj = cls.objects.create(
                patient=medical_record.patient,
                medical_record=medical_record,
                title=rec["title"],
                description=rec["description"]
            )
            rec_objects.append(rec_obj)

        return rec_objects

# -------------------------------
# Vital Model
# -------------------------------
class Vital(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='vitals')
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Vital for {self.patient.user.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"