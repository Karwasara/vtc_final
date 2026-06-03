from django.core.management.base import BaseCommand
from datetime import date
from vtc.views import fetch_biometric_data, store_biometric_data
class Command(BaseCommand):
    help = "Fetch and store biometric attendance data from the external API"
    def handle(self, *args, **options):
        self.stdout.write("Starting biometric synchronization...")
        try:
            today = date.today()
            # Fetch from API
            api_response = fetch_biometric_data(today, today, "")
            # Store in database
            store_biometric_data(api_response)
            self.stdout.write(self.style.SUCCESS("Biometric data synced successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during biometric sync: {str(e)}"))
