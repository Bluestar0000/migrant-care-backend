# HealthBridge/apps.py

from django.apps import AppConfig
import mongoengine

class HealthBridgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "HealthBridge"

    def ready(self):
        
        import HealthBridge.signals
        # Connect to MongoDB (for migrant_care_db)
        mongoengine.disconnect(alias="default")
        mongoengine.connect(
            db="migrant_care_db",
            host="mongodb+srv://Admin:nikh0301@cluster0.eztg1fo.mongodb.net/migrant_care_db?retryWrites=true&w=majority&appName=Cluster0",
            alias="default"
        )

        # Import signals so they are registered when the app is ready
        import HealthBridge.signals