from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta

from syncapp.models import DimFilm
from syncapp.models_source import (
    Film,
    Language,
    Store,
    Staff,
    Address,
    City,
    Country,
)


class IncrementalSyncTest(TestCase):
    databases = {"default", "source"}

    def setUp(self):
        call_command("init", verbosity=0)

    # helper: create required FK rows WITH last_update explicitly provided
    def ensure_source_fks(self):
        now = timezone.now()
        Language.objects.using("source").update_or_create(
            language_id=1,
            defaults={"name": "English", "last_update": now},
        )

        Country.objects.using("source").update_or_create(
            country_id=1,
            defaults={"country": "USA", "last_update": now},
        )

        City.objects.using("source").update_or_create(
            city_id=1,
            defaults={"city": "Chicago", "country_id": 1, "last_update": now},
        )

        Address.objects.using("source").update_or_create(
            address_id=1,
            defaults={
                "address": "123 Test St",
                "district": "District",
                "city_id": 1,
                "postal_code": "00000",
                "phone": "555-1111",
                "last_update": now,
            },
        )

        # create Store first with no manager
        store, _ = Store.objects.using("source").update_or_create(
            store_id=1,
            defaults={
                "manager_staff_id": None,   # 🔥 KEY FIX
                "address_id": 1,
                "last_update": now,
            },
        )

        # create Staff safely
        staff, _ = Staff.objects.using("source").update_or_create(
            staff_id=1,
            defaults={
                "first_name": "Alice",
                "last_name": "Manager",
                "address_id": 1,
                "email": "alice@example.com",
                "store_id": 1,
                "active": 1,
                "username": "alice",
                "last_update": now,
            },
        )

        # give the store its manager
        Store.objects.using("source").filter(store_id=1).update(
            manager_staff_id=1
        )



    # test that incremental loads NEW rows
    def test_incremental_loads_new_records(self):
        self.ensure_source_fks()

        now = timezone.now()

        Film.objects.using("source").update_or_create(
            film_id=2001,
            defaults={
                "title": "TEST MOVIE",
                "description": "Test desc",
                "release_year": 2025,
                "language_id": 1,
                "rental_duration": 3,
                "rental_rate": 0.99,
                "length": 100,
                "replacement_cost": 20,
                "last_update": now,
            },
        )

        call_command("incremental", verbosity=0)

        self.assertTrue(
            DimFilm.objects.filter(film_id=2001).exists(),
            "Incremental sync did NOT load new film.",
        )

    # test that incremental updates existing rows
    def test_incremental_updates_existing_records(self):
        self.ensure_source_fks()
        now = timezone.now()

        # Create original film
        film, _ = Film.objects.using("source").update_or_create(
            film_id=3001,
            defaults={
                "title": "OLD TITLE",
                "description": "orig",
                "release_year": 2024,
                "language_id": 1,
                "rental_duration": 3,
                "rental_rate": 0.99,
                "length": 90,
                "replacement_cost": 20,
                "last_update": now - timedelta(days=1),
            },
        )

        call_command("full_load", verbosity=0)

        film.title = "UPDATED TITLE"
        film.last_update = now
        film.save(using="source")

        call_command("incremental", verbosity=0)

        updated = DimFilm.objects.get(film_id=3001)
        self.assertEqual(
            updated.title,
            "UPDATED TITLE",
            "Incremental sync did NOT propagate film update.",
        )
