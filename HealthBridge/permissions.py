# HealthBridge/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

# -------------------------------
# Role-based permissions
# -------------------------------

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return False
        return u.groups.filter(name="Doctor").exists() or (
            hasattr(u, "profile") and u.profile.role == "doctor"
        )

class IsAuthority(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return False
        return u.groups.filter(name="Authority").exists() or (
            hasattr(u, "profile") and u.profile.role == "authority"
        )

class IsMigrant(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return False
        return u.groups.filter(name="Patient").exists() or (
            hasattr(u, "profile") and u.profile.role in ["migrant", "patient"]
        )

# -------------------------------
# Hospital scoping permissions
# -------------------------------

class SameHospital(BasePermission):
    """
    Allow access only if the object's hospital matches the user's hospital.
    Doctors and authorities are scoped to their hospital.
    Migrants can only access their own records.
    """
    def has_object_permission(self, request, view, obj):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated or not hasattr(u, "profile"):
            return False

        role = u.profile.role

        # Migrant: can only access own object
        if role == "migrant":
            return hasattr(obj, "patient") and obj.patient == u.profile

        # Doctor or authority: hospital must match
        if role in ["doctor", "authority"]:
            user_hospital = getattr(getattr(u, "doctorprofile", None), "hospital", None) \
                            or getattr(getattr(u, "authorityprofile", None), "hospital", None) \
                            or getattr(u.profile, "home_hospital", None)
            obj_hospital = getattr(obj, "hospital", None) or getattr(obj, "home_hospital", None)
            return bool(user_hospital and obj_hospital and user_hospital.id == obj_hospital.id)

        return False


# -------------------------------
# Read-only permission
# -------------------------------

class ReadOnly(BasePermission):
    """Allow safe methods (GET, HEAD, OPTIONS) for everyone authenticated."""
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and request.user.is_authenticated