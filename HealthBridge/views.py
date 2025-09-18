from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import status

class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        role = request.data.get("role")  # optional, if you're using roles

        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "role": role,
                "username": user.username
            })
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



from HealthBridge.models import Profile, MedicalRecord, Scheme, Recommendation
from HealthBridge.serializers import (
    ProfileSerializer,
    MedicalRecordSerializer,
    SchemeSerializer,
    RecommendationSerializer
)
from HealthBridge.utils.recommendation_engine import RecommendationEngine

# 🔹 Role check for Doctor
def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

def home(request):
    return HttpResponse("Welcome to Migrant Care Nexus!")

# 🔹 CRUD APIs

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

@method_decorator(user_passes_test(is_doctor), name='dispatch')
class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

    def perform_create(self, serializer):
        record = serializer.save(updated_by=self.request.user)
        Recommendation.generate_ai_recommendations(record)

    def perform_update(self, serializer):
        record = serializer.save(updated_by=self.request.user)
        Recommendation.generate_ai_recommendations(record)

class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

# 🔹 Hospital Dashboard API

@api_view(["GET"])
def migrant_dashboard_data(request):
    # Fetch data from MongoDB
    return Response({"name": "Asha", "appointments": 3, "alerts": 1})

@api_view(['GET'])
def doctor_dashboard_data(request):
    return Response({"patients": 12, "pendingReports": 4})

@api_view(['GET'])
def authority_dashboard_data(request):
    return Response({"regions": 5, "criticalCases": 2})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def authority_dashboard_metrics(request):
    total_migrants = Profile.objects.count()
    eligible_count = MedicalRecord.objects.filter(eligible_schemes__isnull=False).count()
    ai_alerts = Recommendation.objects.count()
    region_data = (
        Profile.objects
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # 🔹 Disease frequency
    disease_data = (
        MedicalRecord.objects
        .values('recurring_diseases')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return Response({
        "total_migrants": total_migrants,
        "eligible_count": eligible_count,
        "ai_alerts": ai_alerts,
        "region_data": list(region_data),
        "disease_data": list(disease_data)
    })
@permission_classes([IsAuthenticated])
def hospital_dashboard(request, hospital_name):
    if not request.user.groups.filter(name="HospitalAdmin").exists():
        return Response({"error": "Unauthorized"}, status=403)
    records = MedicalRecord.objects.filter(doctor__hospital_name=hospital_name)
    serializer = MedicalRecordSerializer(records, many=True)
    return Response(serializer.data)

# 🔹 Eligible Schemes API

@api_view(["GET"])
def get_eligible_schemes(request, user_id):
    try:
        user = Profile.objects.get(id=user_id)
    except Profile.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    eligible_schemes = Scheme.objects.filter(
        min_age__lte=user.age,
        max_age__gte=user.age,
        gender__in=[user.gender, "ALL"]
    )

    if user.migrant_only:
        eligible_schemes = eligible_schemes.filter(migrant_only=True)

    serializer = SchemeSerializer(eligible_schemes, many=True)
    return Response(serializer.data)

# 🔹 Generate Recommendations API

@api_view(["POST"])
def generate_recommendations(request, user_id):
    try:
        user = Profile.objects.get(id=user_id)
    except Profile.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    schemes = Scheme.objects.filter(
        min_age__lte=user.age,
        max_age__gte=user.age
    )

    recommendations = []
    for scheme in schemes:
        rec = Recommendation.objects.create(
            patient=user,
            title=f"Eligible for {scheme.name}",
            description=scheme.description
        )
        recommendations.append(rec)

    serializer = RecommendationSerializer(recommendations, many=True)
    return Response(serializer.data)

# 🔹 Doctor API: Get patient info via QR code

@api_view(["GET"])
def get_patient_by_qr(request, qr_uuid):
    try:
        record = MedicalRecord.objects.get(qr_code_uuid=qr_uuid)
    except MedicalRecord.DoesNotExist:
        return Response({"error": "Record not found"}, status=404)

    serializer = MedicalRecordSerializer(record)
    return Response(serializer.data)

# 🔹 Doctor API: Get full patient info via QR code

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_full_patient_info_by_qr(request, qr_uuid):
    if not request.user.groups.filter(name="Doctor").exists():
        return Response({"error": "Unauthorized"}, status=403)

    try:
        profile = Profile.objects.get(qr_code_uuid=qr_uuid)
    except Profile.DoesNotExist:
        return Response({"error": "Patient not found"}, status=404)

    medical_records = profile.medical_records.all()
    recommendations = profile.recommendations.all()

    data = {
        "profile": ProfileSerializer(profile).data,
        "medical_records": MedicalRecordSerializer(medical_records, many=True).data,
        "recommendations": RecommendationSerializer(recommendations, many=True).data
    }

    return Response(data)

# 🔹 Authority API: Outbreak summary

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def outbreak_summary(request):
    if not request.user.groups.filter(name="Authority").exists():
        return Response({"error": "Unauthorized"}, status=403)

    data = (
        MedicalRecord.objects
        .values('recurring_diseases')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return Response(data)

# 🔹 Migrant Dashboard API

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dashboard(request, user_id):
    if not request.user.groups.filter(name="Migrant").exists():
        return Response({"error": "Unauthorized"}, status=403)

    try:
        profile = Profile.objects.get(id=user_id)
    except Profile.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    medical_records = MedicalRecord.objects.filter(patient=profile)
    latest_record = medical_records.first()
    schemes = latest_record.eligible_schemes.all() if latest_record else []

    engine = RecommendationEngine(profile, medical_records)
    generated_recommendations = engine.generate()

    return Response({
        "profile": ProfileSerializer(profile).data,
        "medical_record": MedicalRecordSerializer(latest_record).data if latest_record else {},
        "schemes": SchemeSerializer(schemes, many=True).data,
        "recommendations": generated_recommendations
    })
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Profile, Vital
from .serializers import VitalSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_vitals(request, uuid):
    patient = get_object_or_404(Profile, qr_code_uuid=uuid)
    vitals = Vital.objects.filter(patient=patient).order_by("timestamp")
    serializer = VitalSerializer(vitals, many=True)
    return Response(serializer.data)