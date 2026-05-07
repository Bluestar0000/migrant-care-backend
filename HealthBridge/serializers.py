# HealthBridge/serializers.py

from rest_framework import serializers
from .models import (
    Profile,
    MedicalRecord,
    Scheme,
    Recommendation,
    Vital,
)


# ---------------------------
# Patient-facing serializer (safe, concise details for lookups/scans)
# ---------------------------
class PatientProfileSerializer(serializers.ModelSerializer):
    home_hospital_name = serializers.CharField(source="home_hospital.name", read_only=True)
    home_hospital_id = serializers.CharField(source="home_hospital.hospital_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "name",
            "age",
            "gender",
            "language",
            "location",
            "blood_group",
            "migrant_id",
            "awaz_id",
            "qr_code_uuid",
            "home_hospital_id",
            "home_hospital_name",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relation",
        ]

# ---------------------------
# Full profile serializer (admin/API CRUD)
# ---------------------------
class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    home_hospital_name = serializers.CharField(source="home_hospital.name", read_only=True)

    class Meta:
        model = Profile
        fields = "__all__"
        extra_kwargs = {
            "qr_code_image": {"required": False},
            "profile_image": {"required": False},
        }


# ---------------------------
# Medical record serializer
# ---------------------------
class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source="patient.user.username", read_only=True)
    doctor_username = serializers.CharField(source="doctor.user.username", read_only=True)
    hospital_name = serializers.CharField(source="hospital.name", read_only=True)

    class Meta:
        model = MedicalRecord
        fields = "__all__"


# ---------------------------
# Scheme serializer
# ---------------------------
class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = "__all__"


# ---------------------------
# Recommendation serializer
# ---------------------------
class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = "__all__"


# ---------------------------
# Vital serializer
# ---------------------------
class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = "__all__"