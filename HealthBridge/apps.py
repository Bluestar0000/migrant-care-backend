from django.apps import AppConfig

class HealthBridgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'HealthBridge'

    def ready(self):
        import mongoengine
        mongoengine.connect(
            db='migrant_care_db',
            host='mongodb+srv://Admin:nikh0301@cluster0.eztg1fo.mongodb.net/migrant_care_db?retryWrites=true&w=majority&appName=Cluster0',
            alias='default'
        )

        # Import signals inside ready()
        from .signals import create_default_groups
        create_default_groups()