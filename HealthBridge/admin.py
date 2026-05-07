# HealthBridge/admin.py

from django.contrib import admin
from .models import (
    Profile,
    DoctorProfile,
    MedicalRecord,
    Scheme,
    Recommendation,
    Hospital,
    HospitalAdminProfile,
    AuthorityProfile,
)


# ---------------------------
# Patient Profile (Profile model)
# ---------------------------
@admin.register(Profile)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "home_hospital", "migrant_id", "age", "gender", "location")
    search_fields = ("user__username", "migrant_id", "name", "location")
    list_filter = ("home_hospital", "gender", "blood_group", "language")

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"


# ---------------------------
# Doctor Profile
# ---------------------------
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital", "department", "designation")
    search_fields = ("user__username", "hospital__name", "department")
    list_filter = ("hospital", "department")


# ---------------------------
# Medical Record
# ---------------------------
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "hospital", "created_at")
    search_fields = ("patient__user__username", "doctor__user__username", "hospital__name")
    list_filter = ("hospital", "doctor")


# ---------------------------
# Scheme
# ---------------------------
@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


# ---------------------------
# Recommendation
# ---------------------------
@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "content")


# ---------------------------
# Hospital
# ---------------------------
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("hospital_id", "name", "region", "code", "address", "has_key")
    search_fields = ("hospital_id", "name", "region", "code")
    list_filter = ("region",)
    readonly_fields = ("public_key_pem",)

    def has_key(self, obj):
        return bool(obj.public_key_pem)
    has_key.short_description = "Public Key Present"


# ---------------------------
# Hospital Admin Profile
# ---------------------------
@admin.register(HospitalAdminProfile)
class HospitalAdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "hospital")
    search_fields = ("user__username", "hospital__name")
    list_filter = ("hospital",)


# ---------------------------
# Authority Profile
# ---------------------------
@admin.register(AuthorityProfile)
class AuthorityProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "designation")
    search_fields = ("user__username", "department", "designation")
    list_filter = ("department", "designation")