from django.urls import path, include
from rest_framework.routers import DefaultRouter
from HealthBridge.views import get_full_patient_info_by_qr
from django.urls import path
from .views import authority_dashboard_metrics
from django.urls import path
from .views import get_patient_vitals
from .views import CustomLoginView


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
    authority_dashboard_data
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

    
    path('api/patient-full-info/<uuid:qr_uuid>/', get_full_patient_info_by_qr, name='patient-full-info'),
    path('api/migrant/dashboard/', migrant_dashboard_data),
    path('api/doctor/dashboard/', doctor_dashboard_data),
    path('api/authority/dashboard/', authority_dashboard_data),
    path('get_patient_vitals/<uuid:uuid>/', get_patient_vitals),
    path('authority_dashboard_metrics/', authority_dashboard_metrics),
]



    