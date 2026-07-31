from django.core.management.base import BaseCommand
from datetime import date

from vtc.views import (
    fetch_ccl_biometric_data,
    store_ccl_biometric_data,
)


class Command(BaseCommand):
    help = "Fetch and store CCL biometric attendance data"

    def handle(self, *args, **options):

        self.stdout.write(
            "Starting CCL biometric synchronization..."
        )

        try:

            today = date.today()

            # Fetch data from CCL API
            api_response = fetch_ccl_biometric_data(
                today,
                today,
                ""
            )

            # Store data into database
            store_ccl_biometric_data(
                api_response
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "CCL biometric data synced successfully."
                )
            )

        except Exception as e:

            self.stdout.write(
                self.style.ERROR(
                    f"Error during CCL biometric sync: {str(e)}"
                )
            )
