from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
from io import BytesIO
import uuid
import qrcode

# -------------------------------
# Hospital (tenant) model
# -------------------------------
# HealthBridge/models.py

from django.db import models

class Hospital(models.Model):
    hospital_id = models.CharField(max_length=50, unique=True)   # unique hospital identifier
    name = models.CharField(max_length=200, unique=True)         # hospital name
    region = models.CharField(max_length=120, blank=True)        # optional region
    code = models.CharField(max_length=50, blank=True, null=True) # optional code
    address = models.TextField(blank=True, null=True)            # optional address

    # Store public key text (PEM) for verifying signed QR or federated tokens
    public_key_pem = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.hospital_id})"

# -------------------------------
# Profile model
# -------------------------------
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("authority", "Authority"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")

    # Hospital scoping for federated nodes (home facility for the patient)
    home_hospital = models.ForeignKey(
        "Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residents"
    )

    migrant_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, default="Unnamed Patient")
    age = models.IntegerField()
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")]
    )
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True, null=True)
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

    patient_only = models.BooleanField(default=True)
    awaz_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    # Patient QR identifier (local UUID). Always present.
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure a UUID exists
        if not self.qr_code_uuid:
            self.qr_code_uuid = uuid.uuid4()

        # Decide what data goes into QR
        if self.awaz_id:
            qr_data = self.awaz_id
        elif self.migrant_id:
            qr_data = self.migrant_id
        else:
            qr_data = str(self.qr_code_uuid)

        # Regenerate QR if missing or if awaz_id/migrant_id changed
        regenerate_qr = False
        if not self.qr_code_image:
            regenerate_qr = True
        else:
            # Simple heuristic: always regenerate if awaz_id or migrant_id is set
            if self.awaz_id or self.migrant_id:
                regenerate_qr = True

        if regenerate_qr:
            img = qrcode.make(qr_data)
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f"{self.user.username}_qr.png"
            self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    

from django.db import models
from django.contrib.auth.models import User
from .models import Hospital  # if Hospital is in the same app

class HospitalAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Hospital Admin"
        verbose_name_plural = "Hospital Admins"

    def __str__(self):
        return f"{self.user.username} - {self.hospital.name}"


class AuthorityProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Authority"
        verbose_name_plural = "Authorities"

    def __str__(self):
        return f"{self.user.username} ({self.department})"
# -------------------------------
# Scheme model
# -------------------------------
class Scheme(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_age = models.IntegerField()
    max_age = models.IntegerField()
    applicable_diseases = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional: scope scheme to hospital or region if needed
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name="schemes", null=True, blank=True)

    def __str__(self):
        return self.name


# -------------------------------
# Doctor profile model
# -------------------------------
class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="doctors",
        null=True,   # ✅ allow null values in DB
        blank=True   # ✅ allow blank in forms/admin
    )
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        hospital_name = self.hospital.name if self.hospital else "No Hospital"
        return f"{self.user.username} ({hospital_name})"



# -------------------------------
# Medical record model
# -------------------------------
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

from .models import Profile, Hospital, DoctorProfile, Scheme

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='medical_records')

    # Explicit hospital provenance for the record
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name="records",
        null=True,    # ✅ allow null values for existing rows
        blank=True    # ✅ allow blank in forms/admin
    )

    recurring_diseases = models.TextField(blank=True, null=True)
    current_symptoms = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='treated_records'
    )

    treated_at = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    eligible_schemes = models.ManyToManyField(Scheme, blank=True, related_name='beneficiaries')

    # Local QR identifier for the record
    qr_code_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MedicalRecord of {self.patient.user.username} ({self.qr_code_uuid})"

    def assign_schemes(self):
        age = self.patient.age
        diseases = [d.strip().lower() for d in (self.recurring_diseases or "").split(",") if d.strip()]

        # If schemes can be hospital-specific, filter by record's hospital
        eligible = Scheme.objects.filter(min_age__lte=age, max_age__gte=age).filter(
            models.Q(hospital__isnull=True) | models.Q(hospital=self.hospital)
        )

        final_schemes = []
        for scheme in eligible:
            if scheme.applicable_diseases:
                scheme_diseases = [d.strip().lower() for d in scheme.applicable_diseases.split(",") if d.strip()]
                if any(d in diseases for d in scheme_diseases):
                    final_schemes.append(scheme)
            else:
                final_schemes.append(scheme)

        self.eligible_schemes.set(final_schemes)
        self.save()

# -------------------------------
# Recommendation model
# -------------------------------
class Recommendation(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recommendations')
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='recommendations',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_by_patient = models.BooleanField(default=False)

    def __str__(self):
        return f"Recommendation for {self.patient.user.username}: {self.title}"

    @classmethod
    def generate_ai_recommendations(cls, medical_record):
        recommendations = []
        diseases = [d.strip().lower() for d in (medical_record.recurring_diseases or "").split(",") if d.strip()]
        symptoms = [s.strip().lower() for s in (medical_record.current_symptoms or "").split(",") if s.strip()]

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
# Vital model
# -------------------------------
class Vital(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='vitals')
    # Hospital where the vital was recorded (provenance)
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name="vitals", null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Vital for {self.patient.user.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# -------------------------------
# Consent model (optional but recommended for federation)
# -------------------------------
class Consent(models.Model):
    PURPOSE_CHOICES = [
        ("treatment", "Treatment"),
        ("referral", "Referral"),
        ("research", "Research"),
        ("audit", "Audit"),
    ]

    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="consents")
    from_hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name="consents_out")
    to_hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT, related_name="consents_in")
    purpose = models.CharField(max_length=40, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField()
    approved_by_patient = models.BooleanField(default=False)
    approved_by_to_hospital = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["patient", "from_hospital", "to_hospital"]),
        ]

    def is_active(self):
        return (
            self.approved_by_patient
            and self.approved_by_to_hospital
            and timezone.now() < self.expires_at
        )

    def __str__(self):
        return f"Consent[{self.purpose}] {self.patient.name}: {self.from_hospital.name} -> {self.to_hospital.name}"