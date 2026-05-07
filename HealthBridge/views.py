from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Count

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from HealthBridge.models import Profile, MedicalRecord, Scheme, Recommendation, Vital
from HealthBridge.serializers import (
    ProfileSerializer,
    MedicalRecordSerializer,
    SchemeSerializer,
    RecommendationSerializer,
    VitalSerializer,
)
from HealthBridge.utils.recommendation_engine import RecommendationEngine
from HealthBridge.permissions import IsDoctor, IsAuthority, IsMigrant, SameHospital

# HealthBridge/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Profile
from .serializers import PatientProfileSerializer
from uuid import UUID

# HealthBridge/views.py (add a simple view)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def qr_scan_page(request):
    return render(request, "qr_scan.html")

class QRLookupView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # adjust as needed

    def post(self, request):
        value = request.data.get("value", "").strip()
        if not value:
            return Response({"detail": "No value provided"}, status=status.HTTP_400_BAD_REQUEST)

        profile = None

        # Try awaz_id
        if not profile:
            profile = Profile.objects.filter(awaz_id=value).first()

        # Try migrant_id
        if not profile:
            profile = Profile.objects.filter(migrant_id=value).first()

        # Try UUID
        if not profile:
            try:
                UUID(value)  # validate format
                profile = Profile.objects.filter(qr_code_uuid=value).first()
            except ValueError:
                pass

        if not profile:
            return Response({"detail": "No matching profile found"}, status=status.HTTP_404_NOT_FOUND)

        data = PatientProfileSerializer(profile).data
        return Response(data, status=status.HTTP_200_OK)
# -------------------------------
# Authentication
# -------------------------------
class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            try:
                role = user.profile.role.lower()
            except:
                groups = list(user.groups.values_list('name', flat=True))
                role = groups[0].lower() if groups else "patient"
            
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "role": role
            })
        return Response({"error": "Invalid credentials"}, status=401)
def home(request):
    return HttpResponse("Welcome to Migrant Care Nexus!")

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
        serializer = PatientProfileSerializer(profile)
        data = serializer.data
        # Add QR image URL
        if profile.qr_code_image:
            data['qr_code_url'] = request.build_absolute_uri(profile.qr_code_image.url)
        return Response(data)
    except Profile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=404)
# -------------------------------
# CRUD APIs
# -------------------------------
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsDoctor & SameHospital]

    def perform_create(self, serializer):
        record = serializer.save(updated_by=self.request.user)
        Recommendation.generate_ai_recommendations(record)

    def perform_update(self, serializer):
        record = serializer.save(updated_by=self.request.user)
        Recommendation.generate_ai_recommendations(record)


class SchemeViewSet(viewsets.ModelViewSet):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    permission_classes = [IsAuthenticated]


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------
# Dashboards
# -------------------------------
@api_view(["GET"])
@permission_classes([IsMigrant])
def migrant_dashboard_data(request):
    # Example stub data
    return Response({"name": request.user.username, "appointments": 3, "alerts": 1})


@api_view(["GET"])
@permission_classes([IsDoctor])
def doctor_dashboard_data(request):
    return Response({"patients": Profile.objects.count(), "pendingReports": 4})


@api_view(["GET"])
@permission_classes([IsAuthority])
def authority_dashboard_data(request):
    return Response({"regions": 5, "criticalCases": 2})


@api_view(["GET"])
@permission_classes([IsAuthority])
def authority_dashboard_metrics(request):
    total_migrants = Profile.objects.count()
    eligible_count = MedicalRecord.objects.filter(eligible_schemes__isnull=False).count()
    ai_alerts = Recommendation.objects.count()
    region_data = (
        Profile.objects.values('location').annotate(count=Count('id')).order_by('-count')
    )
    disease_data = (
        MedicalRecord.objects.values('recurring_diseases').annotate(count=Count('id')).order_by('-count')
    )
    return Response({
        "total_migrants": total_migrants,
        "eligible_count": eligible_count,
        "ai_alerts": ai_alerts,
        "region_data": list(region_data),
        "disease_data": list(disease_data)
    })


@api_view(["GET"])
@permission_classes([IsAuthority])
def hospital_dashboard(request, hospital_name):
    records = MedicalRecord.objects.filter(doctor__hospital_name=hospital_name)
    serializer = MedicalRecordSerializer(records, many=True)
    return Response(serializer.data)


# -------------------------------
# Schemes & Recommendations
# -------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_eligible_schemes(request, user_id):
    try:
        user = Profile.objects.get(id=user_id)
    except Profile.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    eligible_schemes = Scheme.objects.filter(
        min_age__lte=user.age,
        max_age__gte=user.age
    )
    serializer = SchemeSerializer(eligible_schemes, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsDoctor])
def generate_recommendations(request, user_id):
    try:
        user = Profile.objects.get(id=user_id)
    except Profile.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    schemes = Scheme.objects.filter(min_age__lte=user.age, max_age__gte=user.age)
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


# -------------------------------
# QR-based APIs
# -------------------------------
@api_view(["GET"])
@permission_classes([IsDoctor])
def get_patient_by_qr(request, qr_uuid):
    try:
        record = MedicalRecord.objects.get(qr_code_uuid=qr_uuid)
    except MedicalRecord.DoesNotExist:
        return Response({"error": "Record not found"}, status=404)
    serializer = MedicalRecordSerializer(record)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsDoctor])
def get_full_patient_info_by_qr(request, qr_uuid):
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


# -------------------------------
# Authority API
# -------------------------------
@api_view(["GET"])
@permission_classes([IsAuthority])
def outbreak_summary(request):
    data = (
        MedicalRecord.objects.values('recurring_diseases').annotate(count=Count('id')).order_by('-count')
    )
    return Response(list(data))


# -------------------------------
# Migrant Dashboard
# -------------------------------
@api_view(["GET"])
@permission_classes([IsMigrant])
def user_dashboard(request, user_id):
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
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_symptom_recommendations(request):
    symptoms = request.data.get("symptoms", "")
    if not symptoms:
        return Response({"error": "No symptoms provided"}, status=400)
    
    recommendations = []
    symptoms_lower = symptoms.lower()
    
    if "fever" in symptoms_lower:
        recommendations.append({"title": " Fever Alert", "description": "Take rest, drink plenty of fluids, and consult a doctor if temperature exceeds 103°F or persists beyond 3 days."})
    if "cough" in symptoms_lower:
        recommendations.append({"title": " Respiratory Care", "description": "Persistent cough may indicate respiratory issues. Steam inhalation helps. See a doctor if coughing blood."})
    if "cold" in symptoms_lower:
        recommendations.append({"title": " Cold Relief", "description": "Rest, stay warm, drink warm fluids. Vitamin C helps. Usually resolves in 7-10 days."})
    if "fatigue" in symptoms_lower or "tired" in symptoms_lower:
        recommendations.append({"title": " Energy & Nutrition", "description": "Fatigue can be linked to poor nutrition or stress. Eat iron-rich foods and get 8 hours of sleep."})
    if "headache" in symptoms_lower:
        recommendations.append({"title": " Headache Care", "description": "Stay hydrated, rest in a dark room. If severe or sudden, seek immediate medical attention."})
    if "stomach" in symptoms_lower or "vomit" in symptoms_lower or "nausea" in symptoms_lower:
        recommendations.append({"title": " Digestive Care", "description": "Stick to light foods, stay hydrated with ORS if vomiting. See doctor if pain is severe."})
    if "chest" in symptoms_lower:
        recommendations.append({"title": " Chest Pain - URGENT", "description": "Chest pain can be serious. Please visit a doctor or emergency room immediately."})
    
    if not recommendations:
        recommendations.append({"title": "General Advice", "description": "Please consult a doctor for proper diagnosis. Stay hydrated and get adequate rest."})
    
    return Response({"recommendations": recommendations})
# -------------------------------
# Vitals API
# -------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient_vitals(request, uuid):
    patient = get_object_or_404(Profile, qr_code_uuid=uuid)
    vitals = Vital.objects.filter(patient=patient).order_by("timestamp")
    serializer = VitalSerializer(vitals, many=True)
    return Response(serializer.data)

