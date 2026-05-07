"""
URL configuration for HealChain project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from HealthBridge.views import ai_symptom_recommendations


from HealthBridge.views import (
    ProfileViewSet,
    MedicalRecordViewSet,
    SchemeViewSet,
    RecommendationViewSet,
    get_eligible_schemes,
    generate_recommendations,
    get_patient_by_qr,
    hospital_dashboard,
    outbreak_summary,
    user_dashboard,
    CustomLoginView,
)

# 🔹 Register viewsets with the router
router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'schemes', SchemeViewSet)
router.register(r'recommendations', RecommendationViewSet)

# 🔹 Define URL patterns
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API routes from DRF router
    path('', include(router.urls)),

    # Custom APIs
    path('eligible-schemes/<int:user_id>/', get_eligible_schemes, name='eligible-schemes'),
    path('generate-recommendations/<int:user_id>/', generate_recommendations, name='generate-recommendations'),
    path('get-patient-by-qr/<uuid:qr_uuid>/', get_patient_by_qr, name='get-patient-by-qr'),
    path('hospital-dashboard/<str:hospital_name>/', hospital_dashboard, name='hospital-dashboard'),
    path('outbreak-summary/', outbreak_summary, name='outbreak-summary'),
    path('user-dashboard/<int:user_id>/', user_dashboard, name='user-dashboard'),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/login/', CustomLoginView.as_view(), name='custom-login'),

    # Include HealthBridge app urls (if you have extra routes defined there)
    path('', include('HealthBridge.urls')),
    path('api/ai-recommendations/', ai_symptom_recommendations, name='ai-recommendations'),
]

# 🔹 Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

