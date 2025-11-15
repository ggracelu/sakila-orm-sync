from django.core.management import call_command
from django.test import TestCase
from syncapp.models import DimDate, SyncState

class InitCommandTest(TestCase):

    databases = {"default", "source"}  # use real SQLite database

    def test_init_creates_required_tables(self):
        # run init command
        call_command("init")

        # dim_date should be populated
        self.assertGreater(DimDate.objects.count(), 0)

        # sync_state should contain required entries
        tables = {row.table_name for row in SyncState.objects.all()}
        expected = {
            "film",
            "actor",
            "category",
            "customer",
            "store",
            "rental",
            "payment",
        }
        self.assertTrue(expected.issubset(tables))
