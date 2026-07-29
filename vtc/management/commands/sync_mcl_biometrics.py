from django.core.management.base import BaseCommand
from datetime import date

from vtc.views import (
    fetch_mcl_biometric_data,
    store_mcl_biometric_data,
)


class Command(BaseCommand):
    help = "Fetch and store MCL biometric attendance data"

    def handle(self, *args, **options):

        self.stdout.write("Starting MCL biometric synchronization...")

        try:
            today = date.today()

            # Fetch data from MCL API
            api_response = fetch_mcl_biometric_data(
                today,
                today,
                ""
            )

            # Store data into database
            store_mcl_biometric_data(api_response)

            self.stdout.write(
                self.style.SUCCESS(
                    "MCL biometric data synced successfully."
                )
            )

        except Exception as e:

            self.stdout.write(
                self.style.ERROR(
                    f"Error during MCL biometric sync: {str(e)}"
                )
            )
