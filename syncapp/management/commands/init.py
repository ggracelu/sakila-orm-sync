from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from datetime import date, timedelta

from syncapp.models import DimDate, SyncState


class Command(BaseCommand):
    help = "Initialize the analytics database: create dim_date and sync_state."

    def handle(self, *args, **options):
        self.stdout.write("Running INIT process...")

        # run migrations so analytics tables exist
        self.stdout.write("Ensuring analytics schema is migrated...")
        call_command("migrate", interactive=False)

        # populate dim_date if empty
        if DimDate.objects.count() == 0:
            self.stdout.write("Populating dim_date table...")
            self.populate_dim_date()
        else:
            self.stdout.write("dim_date already populated.")

        # init sync_state rows
        self.stdout.write("Initializing sync_state records...")
        self.init_sync_state()

        # test MySQL connection
        self.stdout.write("Testing MySQL connection...")
        self.test_source_connection()

        self.stdout.write(self.style.SUCCESS("INIT completed successfully!"))

    # func to populate dim_date
    def populate_dim_date(self):
        start = date(1900, 1, 1)
        end = date(2100, 12, 31)

        delta = timedelta(days=1)

        records = []
        current = start

        while current <= end:
            date_key = int(current.strftime("%Y%m%d"))
            records.append(
                DimDate(
                    date_key=date_key,
                    date=current,
                    year=current.year,
                    quarter=((current.month - 1) // 3) + 1,
                    month=current.month,
                    day_of_month=current.day,
                    day_of_week=current.isoweekday(),
                    is_weekend=current.isoweekday() >= 6,
                )
            )
            current += delta

        DimDate.objects.bulk_create(records)
        self.stdout.write(f"   → dim_date populated with {len(records)} rows.")

    # func to nitialize sync_state table
    def init_sync_state(self):
        tables = [
            "film",
            "actor",
            "category",
            "customer",
            "store",
            "rental",
            "payment",
        ]

        for t in tables:
            SyncState.objects.get_or_create(table_name=t)

        self.stdout.write("   → sync_state initialized.")

    # func to test MySQL connection 
    def test_source_connection(self):
        try:
            with connections["source"].cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                if result == (1,):
                    self.stdout.write("   → MySQL connection OK.")
        except Exception as e:
            self.stdout.write(self.style.ERROR("MySQL connection failed: " + str(e)))
            raise
