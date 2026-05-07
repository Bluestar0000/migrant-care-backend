# HealthBridge/utils/groups.py

from django.contrib.auth.models import Group

def create_default_groups():
    """
    Create default role-based groups for the system.
    Roles:
      - Migrant
      - Doctor
      - HospitalAdmin
      - Authority
    """
    roles = ["Migrant", "Doctor", "HospitalAdmin", "Authority"]
    created_groups = []

    for role in roles:
        group, created = Group.objects.get_or_create(name=role)
        if created:
            created_groups.append(role)

    if created_groups:
        print(f"Created groups: {', '.join(created_groups)}")
    else:
        print("All default groups already exist.")