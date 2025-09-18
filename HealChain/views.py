# HealChain/views.py

from rest_framework import viewsets
from HealthBridge.models import Profile, MedicalRecord, Scheme
from HealthBridge.serializers import ProfileSerializer, MedicalRecordSerializer, SchemeSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

# Repeat similarly for MedicalRecordViewSet, SchemeViewSet, etc.