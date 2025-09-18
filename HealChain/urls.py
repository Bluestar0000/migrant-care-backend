"""
URL configuration for HealChain project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
    user_dashboard
)
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from django.urls import path
from .views import CustomLoginView



# 🔹 Register viewsets with the router
router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'schemes', SchemeViewSet)
router.register(r'recommendations', RecommendationViewSet)

# 🔹 Define URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),

    # Custom APIs
    path('eligible-schemes/<int:user_id>/', get_eligible_schemes, name='eligible-schemes'),
    path('generate-recommendations/<int:user_id>/', generate_recommendations, name='generate-recommendations'),
    path('get-patient-by-qr/<uuid:qr_uuid>/', get_patient_by_qr, name='get-patient-by-qr'),
    path('hospital-dashboard/<str:hospital_name>/', hospital_dashboard, name='hospital-dashboard'),
    path('outbreak-summary/', outbreak_summary, name='outbreak-summary'),
    path('user-dashboard/<int:user_id>/', user_dashboard, name='user-dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('HealthBridge.urls')),
    path('api/login/', CustomLoginView.as_view(), name='custom-login'),

]
from django.contrib import admin
from django.urls import path, include

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)