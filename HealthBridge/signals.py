from django.contrib.auth.models import Group

def create_default_groups():
    roles = ["Migrant", "Doctor", "HospitalAdmin", "Authority"]
    for role in roles:
        Group.objects.get_or_create(name=role)