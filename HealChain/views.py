from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Profile  # adjust if your model is elsewhere

class QRLookupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "No code provided"}, status=400)
        
        try:
            profile = Profile.objects.get(qr_code=code)
            return Response({
                "name": profile.user.get_full_name(),
                "age": profile.age,
                "blood_group": profile.blood_group,
                "medical_history": profile.medical_history,
                # add whatever fields your Profile model has
            })
        except Profile.DoesNotExist:
            return Response({"detail": "Patient not found"}, status=404)
class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            groups = list(user.groups.values_list('name', flat=True))
            print("DEBUG groups:", groups)
            role = groups[0].lower() if groups else "patient"
            
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "role": role
            })
        return Response({"error": "Invalid credentials"}, status=401)