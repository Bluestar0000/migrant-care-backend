# HealthBridge/urls.py - CLEAN VERSION
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from HealthBridge.views import ai_symptom_recommendations
from HealthBridge.views import my_profile

from .views import (
    home,
    ProfileViewSet,
    MedicalRecordViewSet,
    SchemeViewSet,
    RecommendationViewSet,
    hospital_dashboard,
    get_eligible_schemes,
    generate_recommendations,
    get_patient_by_qr,
    outbreak_summary,
    user_dashboard,
    migrant_dashboard_data,
    doctor_dashboard_data,
    authority_dashboard_data,
    CustomLoginView,
    QRLookupView,
    get_full_patient_info_by_qr,
    authority_dashboard_metrics,
    get_patient_vitals,
    qr_scan_page,
)

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'schemes', SchemeViewSet)
router.register(r'recommendations', RecommendationViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('api/', include(router.urls)),
    path('api/hospital/<str:hospital_name>/', hospital_dashboard),
    path('api/schemes/<int:user_id>/', get_eligible_schemes),
    path('api/recommend/<int:user_id>/', generate_recommendations),
    path('api/qr/<uuid:qr_uuid>/', get_patient_by_qr),
    path('api/outbreak-summary/', outbreak_summary),
    path('api/dashboard/<int:user_id>/', user_dashboard),
    path('api/login/', CustomLoginView.as_view(), name='custom_login'),
    path('api/patient-full-info/<uuid:qr_uuid>/', get_full_patient_info_by_qr),
    path('api/migrant/dashboard/', migrant_dashboard_data),
    path('api/doctor/dashboard/', doctor_dashboard_data),
    path('api/authority/dashboard/', authority_dashboard_data),
    path('get_patient_vitals/<uuid:uuid>/', get_patient_vitals),
    path('authority_dashboard_metrics/', authority_dashboard_metrics),
    path('scan/', qr_scan_page, name='qr-scan'),
    path('api/qr-lookup/', QRLookupView.as_view(), name='qr-lookup'),
    path('api/ai-recommendations/', ai_symptom_recommendations, name='ai-recommendations'),
    path('api/my-profile/', my_profile, name='my-profile'),
]

