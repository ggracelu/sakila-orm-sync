from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from syncapp.models_source import (
    Film,
    Actor,
    Category,
    FilmActor,
    Store,
    Customer,
    Inventory,
    Rental,
    Payment,
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
    DimDate,
)


class Command(BaseCommand):
    help = "Full reload of all analytics tables from Sakila (MySQL → SQLite)."

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting FULL LOAD (complete refresh of analytics DB)...")

        with transaction.atomic():
            # clear analytics tables
            self.clear_target_tables()

            # load dims
            self.load_dim_film()
            self.load_dim_actor()
            self.load_dim_category()
            self.load_dim_store()
            self.load_dim_customer()
            # load bridges
            self.load_bridge_film_actor()
            self.load_bridge_film_category()
            # load facts
            self.load_fact_rental()
            self.load_fact_payment()
            # update sync_state timestamps
            self.update_sync_state()

        self.stdout.write(self.style.SUCCESS("🎉 FULL LOAD completed successfully!"))

    # clear all analytics tables completely
    def clear_target_tables(self):
        self.stdout.write("🧹 Clearing existing analytics tables...")

        FactPayment.objects.all().delete()
        FactRental.objects.all().delete()
        BridgeFilmCategory.objects.all().delete()
        BridgeFilmActor.objects.all().delete()

        DimCustomer.objects.all().delete()
        DimStore.objects.all().delete()
        DimCategory.objects.all().delete()
        DimActor.objects.all().delete()
        DimFilm.objects.all().delete()

        self.stdout.write("   → Target tables cleared.")

    # dimensions
    def load_dim_film(self):
        self.stdout.write("🎬 Loading dim_film...")

        records = []
        for film in Film.objects.using("source").all():
            records.append(
                DimFilm(
                    film_id=film.film_id,
                    title=film.title,
                    rating=film.rating or "",
                    length=film.length,
                    language=film.language.name,
                    release_year=film.release_year,
                    last_update=film.last_update,
                )
            )

        DimFilm.objects.bulk_create(records)
        self.stdout.write(f"   → dim_film: {len(records)} rows loaded.")

    def load_dim_actor(self):
        self.stdout.write("🎭 Loading dim_actor...")

        records = []
        for actor in Actor.objects.using("source").all():
            records.append(
                DimActor(
                    actor_id=actor.actor_id,
                    first_name=actor.first_name,
                    last_name=actor.last_name,
                    last_update=actor.last_update,
                )
            )
        DimActor.objects.bulk_create(records)
        self.stdout.write(f"   → dim_actor: {len(records)} rows loaded.")

    def load_dim_category(self):
        self.stdout.write("🏷️  Loading dim_category...")

        records = []
        for cat in Category.objects.using("source").all():
            records.append(
                DimCategory(
                    category_id=cat.category_id,
                    name=cat.name,
                    last_update=cat.last_update,
                )
            )
        DimCategory.objects.bulk_create(records)
        self.stdout.write(f"   → dim_category: {len(records)} rows loaded.")

    def load_dim_store(self):
        self.stdout.write("🏬 Loading dim_store...")

        records = []
        stores = Store.objects.using("source").select_related("address__city__country")

        for store in stores:
            addr = store.address
            city = addr.city
            country = city.country

            records.append(
                DimStore(
                    store_id=store.store_id,
                    city=city.city,
                    country=country.country,
                    last_update=store.last_update,
                )
            )

        DimStore.objects.bulk_create(records)
        self.stdout.write(f"   → dim_store: {len(records)} rows loaded.")

    def load_dim_customer(self):
        self.stdout.write("👤 Loading dim_customer...")

        records = []
        customers = Customer.objects.using("source").select_related("address__city__country")

        for cust in customers:
            addr = cust.address
            city = addr.city
            country = city.country

            records.append(
                DimCustomer(
                    customer_id=cust.customer_id,
                    first_name=cust.first_name,
                    last_name=cust.last_name,
                    active=cust.active,
                    city=city.city,
                    country=country.country,
                    last_update=cust.last_update,
                )
            )

        DimCustomer.objects.bulk_create(records)
        self.stdout.write(f"   → dim_customer: {len(records)} rows loaded.")

    # bridge tables
    def load_bridge_film_actor(self):
        self.stdout.write("🔗 Loading bridge_film_actor...")

        records = []
        links = FilmActor.objects.using("source").all()

        for link in links:
            try:
                film_key = DimFilm.objects.get(film_id=link.film_id).film_key
                actor_key = DimActor.objects.get(actor_id=link.actor_id).actor_key

                records.append(
                    BridgeFilmActor(
                        film_key_id=film_key,
                        actor_key_id=actor_key,
                    )
                )
            except Exception:
                continue

        BridgeFilmActor.objects.bulk_create(records)
        self.stdout.write(f"   → bridge_film_actor: {len(records)} rows loaded.")

    def load_bridge_film_category(self):
        self.stdout.write("🔗 Loading bridge_film_category...")

        from syncapp.models_source import FilmCategory  # import inside method to avoid circular

        records = []
        links = FilmCategory.objects.using("source").all()

        for link in links:
            film_key = DimFilm.objects.get(film_id=link.film_id).film_key
            category_key = DimCategory.objects.get(category_id=link.category_id).category_key

            records.append(
                BridgeFilmCategory(
                    film_key_id=film_key,
                    category_key_id=category_key,
            )
        )

        BridgeFilmCategory.objects.bulk_create(records)
        self.stdout.write(f"   → bridge_film_category: {len(records)} rows loaded.")

    # fact tables
    def load_fact_rental(self):
        self.stdout.write("📀 Loading fact_rental...")

        records = []
        rentals = Rental.objects.using("source").select_related(
            "inventory__film", "customer", "inventory__store"
        )

        for r in rentals:
            film_key = DimFilm.objects.get(film_id=r.inventory.film_id).film_key
            store_key = DimStore.objects.get(store_id=r.inventory.store_id).store_key
            customer_key = DimCustomer.objects.get(customer_id=r.customer_id).customer_key

            date_key_rented = int(r.rental_date.strftime("%Y%m%d"))
            date_key_returned = (
                int(r.return_date.strftime("%Y%m%d")) if r.return_date else None
            )

            rental_duration = (
                (r.return_date - r.rental_date).days
                if r.return_date
                else None
            )

            records.append(
                FactRental(
                    rental_id=r.rental_id,
                    date_key_rented_id=date_key_rented,
                    date_key_returned_id=date_key_returned,
                    film_key_id=film_key,
                    store_key_id=store_key,
                    customer_key_id=customer_key,
                    staff_id=r.staff_id,
                    rental_duration_days=rental_duration,
                )
            )

        FactRental.objects.bulk_create(records)
        self.stdout.write(f"   → fact_rental: {len(records)} rows loaded.")

    def load_fact_payment(self):
        self.stdout.write("💰 Loading fact_payment...")

        records = []
        payments = Payment.objects.using("source").all()

        for p in payments:
            customer_key = DimCustomer.objects.get(customer_id=p.customer_id).customer_key
            store_key = DimStore.objects.get(store_id=p.staff.store_id).store_key
            date_key = int(p.payment_date.strftime("%Y%m%d"))

            records.append(
                FactPayment(
                    payment_id=p.payment_id,
                    date_key_paid_id=date_key,
                    customer_key_id=customer_key,
                    store_key_id=store_key,
                    staff_id=p.staff_id,
                    amount=p.amount,
                )
            )

        FactPayment.objects.bulk_create(records)
        self.stdout.write(f"   → fact_payment: {len(records)} rows loaded.")

    # sync state
    def update_sync_state(self):
        now = timezone.now()

        for table in [
            "film",
            "actor",
            "category",
            "store",
            "customer",
            "rental",
            "payment",
        ]:
            SyncState.objects.filter(table_name=table).update(last_update=now)

        self.stdout.write("   → sync_state timestamps updated.")
