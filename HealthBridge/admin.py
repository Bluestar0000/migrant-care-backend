from django.contrib import admin
from .models import Profile, DoctorProfile, MedicalRecord, Scheme, Recommendation

admin.site.register(Profile)
admin.site.register(DoctorProfile)
admin.site.register(MedicalRecord)
admin.site.register(Scheme)
admin.site.register(Recommendation)

# Register your models here.
