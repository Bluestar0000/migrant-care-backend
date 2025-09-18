from rest_framework import serializers
from .models import Profile, MedicalRecord, Scheme, Recommendation

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        extra_kwargs = {
            'qr_code_image': {'required': False},
            'profile_image': {'required': False}
        }

class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = '__all__'

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'
from rest_framework import serializers
from .models import Vital

class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = "__all__"