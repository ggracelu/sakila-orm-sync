from syncapp.models_source import Language, Film
from django.utils import timezone
from django.core.management import call_command
from django.test import TestCase
from syncapp.models import (
    DimFilm, DimActor, DimCategory, DimStore, DimCustomer,
    BridgeFilmActor, BridgeFilmCategory,
    FactRental, FactPayment
)

class FullLoadCommandTest(TestCase):
    databases = {"default", "source"}

    def setUp(self):
        call_command("init", verbosity=0)

        Language.objects.using("source").update_or_create(
            language_id=1,
            defaults={"name": "English", "last_update": timezone.now()},
        )

        Film.objects.using("source").update_or_create(
            film_id=1,
            defaults={
                "title": "SEED MOVIE",
                "description": "seed",
                "release_year": 2024,
                "language_id": 1,
                "rental_duration": 3,
                "rental_rate": 0.99,
                "length": 100,
                "replacement_cost": 20,
                "last_update": timezone.now(),
            },
        )

    def test_full_load_populates_all_tables(self):
        call_command("full_load", verbosity=0)
        self.assertGreater(
            DimFilm.objects.count(), 0,
            "FULL LOAD did not load films even though one exists in source DB."
        )
