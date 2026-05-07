# HealChain — HealthBridge Backend API

Django REST Framework backend for the MigrantCare platform — a healthcare system for migrant workers with role-based access, QR patient identification, and outbreak monitoring.

## Live API
https://migrant-care-backend.onrender.com

## Tech Stack
- Python 3.13 / Django 6.0
- Django REST Framework
- MongoDB (MongoEngine) + SQLite
- MongoDB Atlas (cloud)
- Deployed on Render

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/login/ | None | Role-based login — returns token + role |
| GET | /api/my-profile/ | Token | Logged-in patient profile + QR URL |
| POST | /api/qr-lookup/ | Token | Doctor patient lookup by migrant ID or UUID |
| POST | /api/ai-recommendations/ | Token | Symptom-based health recommendations |
| GET | /api/outbreak-summary/ | Token | Disease outbreak data by type |
| GET | /authority_dashboard_metrics/ | Token | Region metrics, total migrants, AI alerts |
| GET | /api/profiles/ | Token | All patient profiles |
| GET | /api/medical-records/ | Token | Medical records |
| GET | /api/schemes/ | Token | Government health schemes |

## Roles

| Role | Access |
|------|--------|
| Patient | Own profile, QR code, symptoms, recommendations |
| Doctor | QR patient lookup, medical records |
| Authority | Outbreak data, region metrics, alerts |

## Local Setup

```bash
git clone https://github.com/Bluestar0000/HealChain
cd HealChain
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
MONGO_URI=mongodb+srv://...
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

Run:
```bash
python manage.py migrate
python manage.py runserver
```

## Key Features
- Token-based authentication with role detection from user groups
- QR code auto-generation on patient profile creation
- RSA key pair generation per hospital for federation
- MongoEngine integration for migrant document storage
- Rule-based AI recommendation engine for 7+ symptoms
- Outbreak monitoring with region-level disease tracking
