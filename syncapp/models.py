from django.db import models

# dimension tables
class DimDate(models.Model):
    """
    Date dimension: one row per calendar date.
    date_key: surrogate integer key in YYYYMMDD form.
    """
    date_key = models.IntegerField(primary_key=True)  # e.g., 20060214
    date = models.DateField()
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField()
    day_of_month = models.IntegerField()
    day_of_week = models.IntegerField()  # 1=Monday..7=Sunday, or similar convention
    is_weekend = models.BooleanField()

    class Meta:
        db_table = "dim_date"
        indexes = [
            models.Index(fields=["year", "month"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.date} ({self.date_key})"


class DimFilm(models.Model):
    """
    Film dimension. film_id is the natural key from Sakila.
    film_key is the surrogate key used in analytics schema.
    """
    film_key = models.AutoField(primary_key=True)
    film_id = models.IntegerField(unique=True)  # Sakila film.film_id
    title = models.CharField(max_length=255)
    rating = models.CharField(max_length=10, null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50)
    release_year = models.IntegerField(null=True, blank=True)
    last_update = models.DateTimeField()

    class Meta:
        db_table = "dim_film"
        indexes = [
            models.Index(fields=["film_id"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"{self.title} (film_id={self.film_id})"


class DimActor(models.Model):
    actor_key = models.AutoField(primary_key=True)
    actor_id = models.IntegerField(unique=True)  # Sakila actor.actor_id
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    last_update = models.DateTimeField()

    class Meta:
        db_table = "dim_actor"
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["actor_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} (actor_id={self.actor_id})"


class DimCategory(models.Model):
    category_key = models.AutoField(primary_key=True)
    category_id = models.IntegerField(unique=True)  # Sakila category.category_id
    name = models.CharField(max_length=25)
    last_update = models.DateTimeField()

    class Meta:
        db_table = "dim_category"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category_id"]),
        ]

    def __str__(self):
        return f"{self.name} (category_id={self.category_id})"


class DimStore(models.Model):
    store_key = models.AutoField(primary_key=True)
    store_id = models.IntegerField(unique=True)  # Sakila store.store_id
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    last_update = models.DateTimeField()

    class Meta:
        db_table = "dim_store"
        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
            models.Index(fields=["store_id"]),
        ]

    def __str__(self):
        return f"Store {self.store_id} - {self.city}, {self.country}"


class DimCustomer(models.Model):
    customer_key = models.AutoField(primary_key=True)
    customer_id = models.IntegerField(unique=True)  # Sakila customer.customer_id
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    active = models.BooleanField()
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    last_update = models.DateTimeField()

    class Meta:
        db_table = "dim_customer"
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
            models.Index(fields=["customer_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} (customer_id={self.customer_id})"



# bridge tables

class BridgeFilmActor(models.Model):
    """
    Bridge between DimFilm and DimActor.
    """
    id = models.AutoField(primary_key=True)
    film_key = models.ForeignKey(DimFilm, on_delete=models.CASCADE)
    actor_key = models.ForeignKey(DimActor, on_delete=models.CASCADE)

    class Meta:
        db_table = "bridge_film_actor"
        unique_together = ("film_key", "actor_key")
        indexes = [
            models.Index(fields=["film_key"]),
            models.Index(fields=["actor_key"]),
        ]

    def __str__(self):
        return f"FilmKey {self.film_key_id} - ActorKey {self.actor_key_id}"


class BridgeFilmCategory(models.Model):
    """
    Bridge between DimFilm and DimCategory.
    """
    id = models.AutoField(primary_key=True)
    film_key = models.ForeignKey(DimFilm, on_delete=models.CASCADE)
    category_key = models.ForeignKey(DimCategory, on_delete=models.CASCADE)

    class Meta:
        db_table = "bridge_film_category"
        unique_together = ("film_key", "category_key")
        indexes = [
            models.Index(fields=["film_key"]),
            models.Index(fields=["category_key"]),
        ]

    def __str__(self):
        return f"FilmKey {self.film_key_id} - CategoryKey {self.category_key_id}"



# fact tables

class FactRental(models.Model):
    """
    Rental fact table: one row per rental.
    """
    fact_rental_key = models.AutoField(primary_key=True)
    rental_id = models.IntegerField(unique=True)  # Sakila rental.rental_id

    date_key_rented = models.ForeignKey(
        DimDate,
        on_delete=models.PROTECT,
        related_name="rentals_rented_on",
        db_column="date_key_rented",
    )
    date_key_returned = models.ForeignKey(
        DimDate,
        on_delete=models.PROTECT,
        related_name="rentals_returned_on",
        db_column="date_key_returned",
        null=True,
        blank=True,
    )

    film_key = models.ForeignKey(DimFilm, on_delete=models.PROTECT)
    store_key = models.ForeignKey(DimStore, on_delete=models.PROTECT)
    customer_key = models.ForeignKey(DimCustomer, on_delete=models.PROTECT)

    staff_id = models.IntegerField()  # staff natural key from Sakila
    rental_duration_days = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "fact_rental"
        indexes = [
            models.Index(fields=["rental_id"]),
            models.Index(fields=["date_key_rented"]),
            models.Index(fields=["date_key_returned"]),
            models.Index(fields=["film_key"]),
            models.Index(fields=["store_key"]),
            models.Index(fields=["customer_key"]),
        ]

    def __str__(self):
        return f"Rental {self.rental_id}"


class FactPayment(models.Model):
    """
    Payment fact table: one row per payment transaction.
    """
    fact_payment_key = models.AutoField(primary_key=True)
    payment_id = models.IntegerField(unique=True)  # Sakila payment.payment_id

    date_key_paid = models.ForeignKey(
        DimDate,
        on_delete=models.PROTECT,
        related_name="payments_paid_on",
        db_column="date_key_paid",
    )
    customer_key = models.ForeignKey(DimCustomer, on_delete=models.PROTECT)
    store_key = models.ForeignKey(DimStore, on_delete=models.PROTECT)

    staff_id = models.IntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = "fact_payment"
        indexes = [
            models.Index(fields=["payment_id"]),
            models.Index(fields=["date_key_paid"]),
            models.Index(fields=["customer_key"]),
            models.Index(fields=["store_key"]),
        ]

    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount}"



# sync state table

class SyncState(models.Model):
    """
    Tracks the last update timestamp for each logical source table
    (e.g. 'film', 'actor', 'rental', 'payment', 'customer', etc.).
    """
    table_name = models.CharField(max_length=50, unique=True)
    last_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sync_state"

    def __str__(self):
        return f"{self.table_name}: {self.last_update}"
