from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from syncapp.models_source import (
    Film,
    Actor,
    Category,
    Customer,
    Store,
    Rental,
    Payment,
)
from syncapp.models import (
    DimFilm,
    DimActor,
    DimCategory,
    DimCustomer,
    DimStore,
    FactRental,
    FactPayment,
)


class Command(BaseCommand):
    help = "Validate data consistency between MySQL (source) and SQLite (analytics)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to validate (default: 30)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        self.stdout.write(f"Running VALIDATION checks for the last {days} days...")

        self.check_counts()
        self.check_recent_rentals(days)
        self.check_recent_payments(days)
        self.check_payment_totals(days)

        self.stdout.write(self.style.SUCCESS("Validation completed."))

    # dim counts
    def check_counts(self):
        self.stdout.write("\nChecking dimension table counts...")

        checks = [
            ("Films", Film.objects.using("source").count(), DimFilm.objects.count()),
            ("Actors", Actor.objects.using("source").count(), DimActor.objects.count()),
            ("Categories", Category.objects.using("source").count(), DimCategory.objects.count()),
            ("Customers", Customer.objects.using("source").count(), DimCustomer.objects.count()),
            ("Stores", Store.objects.using("source").count(), DimStore.objects.count()),
        ]

        for label, src, tgt in checks:
            if src == tgt:
                self.stdout.write(f"   ✔ {label}: {src} rows (OK)")
            else:
                self.stdout.write(self.style.ERROR(
                    f"   ✖ {label}: SOURCE={src} TARGET={tgt} (Mismatch!)"
                ))

    # rentals
    def check_recent_rentals(self, days):
        self.stdout.write("\n📀 Checking rentals...")

        cutoff = timezone.now() - timedelta(days=days)

        src = Rental.objects.using("source").filter(rental_date__gte=cutoff).count()
        tgt = FactRental.objects.filter(date_key_rented__date__gte=cutoff.date()).count()

        if src == tgt:
            self.stdout.write(f"   ✔ Rentals: {src} rows match (OK)")
        else:
            self.stdout.write(self.style.ERROR(
                f"   ✖ Rentals mismatch: SOURCE={src} TARGET={tgt}"
            ))

    # payments
    def check_recent_payments(self, days):
        self.stdout.write("\n💰 Checking payments...")

        cutoff = timezone.now() - timedelta(days=days)

        src = Payment.objects.using("source").filter(payment_date__gte=cutoff).count()
        tgt = FactPayment.objects.filter(date_key_paid__date__gte=cutoff.date()).count()

        if src == tgt:
            self.stdout.write(f"   ✔ Payments: {src} rows match (OK)")
        else:
            self.stdout.write(self.style.ERROR(
                f"   ✖ Payments mismatch: SOURCE={src} TARGET={tgt}"
            ))

    # revenue totals
    def check_payment_totals(self, days):
        self.stdout.write("\nChecking payment totals...")

        cutoff = timezone.now() - timedelta(days=days)

        src_total = (
            Payment.objects.using("source")
            .filter(payment_date__gte=cutoff)
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

        tgt_total = (
            FactPayment.objects
            .filter(date_key_paid__date__gte=cutoff.date())
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

        if abs(src_total - tgt_total) < 0.01:
            self.stdout.write(f"   ✔ Revenue totals match: ${src_total:.2f} (OK)")
        else:
            self.stdout.write(self.style.ERROR(
                f"   ✖ Revenue mismatch: SOURCE=${src_total:.2f} TARGET=${tgt_total:.2f}"
            ))
