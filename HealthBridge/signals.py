# HealthBridge/signals.py

import os
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.contrib.auth.models import Group, Permission
from .models import Hospital, DoctorProfile, Profile, HospitalAdminProfile, AuthorityProfile

import qrcode
from io import BytesIO
from django.core.files import File

@receiver(post_save, sender=Profile)
def generate_patient_qr(sender, instance, created, **kwargs):
    if not instance.qr_code_image or created:
        qr_data = instance.migrant_id or str(instance.qr_code_uuid)
        
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)
        
        filename = f"{instance.user.username}_qr.png"
        instance.qr_code_image.save(filename, File(buffer), save=False)
        Profile.objects.filter(pk=instance.pk).update(qr_code_image=instance.qr_code_image.name)
@receiver(post_save, sender=Hospital)
def generate_hospital_key(sender, instance, created, **kwargs):
    """
    Automatically generate an RSA key pair when a new Hospital is created.
    - Public key PEM is stored in the Hospital model (for verification/federation).
    - Private key PEM is written to local 'keys/' directory (for testing only).
    """
    if created and not instance.public_key_pem:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        instance.public_key_pem = public_pem
        instance.save(update_fields=["public_key_pem"])

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        os.makedirs("keys", exist_ok=True)
        private_key_path = os.path.join("keys", f"{instance.hospital_id}_private.pem")
        with open(private_key_path, "w", encoding="utf-8") as f:
            f.write(private_pem)


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Create default role-based groups and assign permissions.
    Roles:
      - Patient
      - Doctor
      - HospitalAdmin
      - Authority
    """
    roles = ["Patient", "Doctor", "HospitalAdmin", "Authority"]
    for role in roles:
        group, _ = Group.objects.get_or_create(name=role)

        if role == "Patient":
            perms = Permission.objects.filter(codename__in=["view_medicalrecord"])
        elif role == "Doctor":
            perms = Permission.objects.filter(codename__in=[
                "add_medicalrecord", "change_medicalrecord", "view_medicalrecord"
            ])
        elif role == "HospitalAdmin":
            perms = Permission.objects.filter(codename__in=[
                "add_doctorprofile", "change_doctorprofile", "view_doctorprofile",
                "add_hospital", "change_hospital", "view_hospital"
            ])
        elif role == "Authority":
            perms = Permission.objects.filter(codename__in=[
                "view_medicalrecord", "view_profile", "view_hospital"
            ])
        else:
            perms = []

        group.permissions.set(perms)


@receiver(post_save, sender=DoctorProfile)
def assign_doctor_group(sender, instance, created, **kwargs):
    """
    Automatically assign the linked user to the 'Doctor' group when a DoctorProfile is created.
    """
    if created:
        doctor_group, _ = Group.objects.get_or_create(name="Doctor")
        user = instance.user
        if doctor_group not in user.groups.all():
            user.groups.add(doctor_group)
            user.save()


@receiver(post_save, sender=Profile)
def assign_patient_group(sender, instance, created, **kwargs):
    """
    Automatically assign the linked user to the 'Patient' group when a Profile is created.
    """
    if created:
        patient_group, _ = Group.objects.get_or_create(name="Patient")
        user = instance.user
        if patient_group not in user.groups.all():
            user.groups.add(patient_group)
            user.save()


@receiver(post_save, sender=HospitalAdminProfile)
def assign_hospital_admin_group(sender, instance, created, **kwargs):
    """
    Automatically assign the linked user to the 'HospitalAdmin' group when a HospitalAdminProfile is created.
    """
    if created:
        admin_group, _ = Group.objects.get_or_create(name="HospitalAdmin")
        user = instance.user
        if admin_group not in user.groups.all():
            user.groups.add(admin_group)
            user.save()


@receiver(post_save, sender=AuthorityProfile)
def assign_authority_group(sender, instance, created, **kwargs):
    """
    Automatically assign the linked user to the 'Authority' group when an AuthorityProfile is created.
    """
    if created:
        authority_group, _ = Group.objects.get_or_create(name="Authority")
        user = instance.user
        if authority_group not in user.groups.all():
            user.groups.add(authority_group)
            user.save()