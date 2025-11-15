from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from syncapp.models_source import (
    Film,
    Actor,
    Category,
    Customer,
    Store,
    Rental,
    Payment,
    FilmActor,
    FilmCategory,
)
from syncapp.models import (
    DimFilm,
    DimActor,
    DimCategory,
    DimStore,
    DimCustomer,
    BridgeFilmActor,
    BridgeFilmCategory,
    FactRental,
    FactPayment,
    SyncState,
)


class Command(BaseCommand):
    help = "Incremental sync from MySQL Sakila into SQLite analytics warehouse."

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting INCREMENTAL SYNC...")

        with transaction.atomic():
            self.sync_films()
            self.sync_actors()
            self.sync_categories()
            self.sync_stores()
            self.sync_customers()
            self.sync_rentals()
            self.sync_payments()
            self.update_sync_state()

        self.stdout.write(self.style.SUCCESS("🎉 Incremental sync completed!"))

    # helpers
    def get_last_sync(self, table_name):
        state = SyncState.objects.get(table_name=table_name)
        return state.last_update

    def set_sync(self, table_name, timestamp):
        SyncState.objects.filter(table_name=table_name).update(last_update=timestamp)

    # dimension tables
    def sync_films(self):
        self.stdout.write("🎬 Incremental sync: films")

        last = self.get_last_sync("film") or datetime(1900, 1, 1)

        # Only fetch changed/new films
        updated = Film.objects.using("source").filter(last_update__gt=last)

        count = 0
        for f in updated:
            DimFilm.objects.update_or_create(
                film_id=f.film_id,
                defaults={
                    "title": f.title,
                    "rating": f.rating or "",
                    "length": f.length,
                    "language": f.language.name,
                    "release_year": f.release_year,
                    "last_update": f.last_update,
                },
            )
            count += 1

        self.stdout.write(f"   → Updated/created {count} films.")


    def sync_actors(self):
        self.stdout.write("🎭 Incremental sync: actors")

        last = self.get_last_sync("actor") or datetime(1900, 1, 1)

        updated = Actor.objects.using("source").filter(last_update__gt=last)

        for a in updated:
            DimActor.objects.update_or_create(
                actor_id=a.actor_id,
                defaults={
                    "first_name": a.first_name,
                    "last_name": a.last_name,
                    "last_update": a.last_update,
                },
            )

        self.stdout.write(f"   → Updated/created {updated.count()} actors.")

    def sync_categories(self):
        self.stdout.write("🏷️  Incremental sync: categories")

        last = self.get_last_sync("category") or datetime(1900, 1, 1)

        updated = Category.objects.using("source").filter(last_update__gt=last)

        for c in updated:
            DimCategory.objects.update_or_create(
                category_id=c.category_id,
                defaults={
                    "name": c.name,
                    "last_update": c.last_update,
                },
            )

        self.stdout.write(f"   → Updated/created {updated.count()} categories.")

    def sync_stores(self):
        self.stdout.write("🏬 Incremental sync: stores")

        last = self.get_last_sync("store") or datetime(1900, 1, 1)

        updated = Store.objects.using("source").filter(last_update__gt=last)

        for s in updated:
            addr = s.address
            city = addr.city
            country = city.country

            DimStore.objects.update_or_create(
                store_id=s.store_id,
                defaults={
                    "city": city.city,
                    "country": country.country,
                    "last_update": s.last_update,
                },
            )

        self.stdout.write(f"   → Updated/created {updated.count()} stores.")

    def sync_customers(self):
        self.stdout.write("👤 Incremental sync: customers")

        last = self.get_last_sync("customer") or datetime(1900, 1, 1)

        updated = Customer.objects.using("source").filter(last_update__gt=last)

        for c in updated:
            addr = c.address
            city = addr.city
            country = city.country

            DimCustomer.objects.update_or_create(
                customer_id=c.customer_id,
                defaults={
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "active": c.active,
                    "city": city.city,
                    "country": country.country,
                    "last_update": c.last_update,
                },
            )

        self.stdout.write(f"   → Updated/created {updated.count()} customers.")

    # fact tables
    def sync_rentals(self):
        self.stdout.write("📀 Incremental sync: rentals")

        last = self.get_last_sync("rental") or datetime(1900, 1, 1)

        updated = Rental.objects.using("source").filter(
            last_update__gt=last
        ).select_related("inventory__film", "inventory__store", "customer")

        count = 0
        for r in updated:
            film_key = DimFilm.objects.get(film_id=r.inventory.film_id).film_key
            store_key = DimStore.objects.get(store_id=r.inventory.store_id).store_key
            customer_key = DimCustomer.objects.get(customer_id=r.customer_id).customer_key

            date_key_rented = int(r.rental_date.strftime("%Y%m%d"))
            date_key_returned = (
                int(r.return_date.strftime("%Y%m%d")) if r.return_date else None
            )

            rental_duration = (
                (r.return_date - r.rental_date).days if r.return_date else None
            )

            FactRental.objects.update_or_create(
                rental_id=r.rental_id,
                defaults={
                    "date_key_rented_id": date_key_rented,
                    "date_key_returned_id": date_key_returned,
                    "film_key_id": film_key,
                    "store_key_id": store_key,
                    "customer_key_id": customer_key,
                    "staff_id": r.staff_id,
                    "rental_duration_days": rental_duration,
                },
            )
            count += 1

        self.stdout.write(f"   → Upserted {count} rentals.")

    def sync_payments(self):
        self.stdout.write("💰 Incremental sync: payments")

        last = self.get_last_sync("payment") or datetime(1900, 1, 1)

        updated = Payment.objects.using("source").filter(payment_date__gt=last)

        count = 0
        for p in updated:
            customer_key = DimCustomer.objects.get(customer_id=p.customer_id).customer_key
            store_key = DimStore.objects.get(store_id=p.staff.store_id).store_key
            date_key = int(p.payment_date.strftime("%Y%m%d"))

            FactPayment.objects.update_or_create(
                payment_id=p.payment_id,
                defaults={
                    "date_key_paid_id": date_key,
                    "customer_key_id": customer_key,
                    "store_key_id": store_key,
                    "staff_id": p.staff_id,
                    "amount": p.amount,
                },
            )
            count += 1

        self.stdout.write(f"   → Upserted {count} payments.")

    # sync state

    def update_sync_state(self):
        now = timezone.now()
        for table in [
            "film",
            "actor",
            "category",
            "customer",
            "store",
            "rental",
            "payment",
        ]:
            self.set_sync(table, now)

        self.stdout.write("   → Sync state updated.")
