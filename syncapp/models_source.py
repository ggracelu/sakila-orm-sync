from django.db import models

# managed = False so django does not touch these tables

class Language(models.Model):
    language_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "language"


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    language = models.ForeignKey(Language, models.DO_NOTHING, db_column="language_id")
    rental_duration = models.IntegerField()
    rental_rate = models.DecimalField(max_digits=4, decimal_places=2)
    length = models.IntegerField(null=True, blank=True)
    replacement_cost = models.DecimalField(max_digits=5, decimal_places=2)
    rating = models.CharField(max_length=10, null=True, blank=True)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "film"


class Actor(models.Model):
    actor_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "actor"


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=25)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "category"


class FilmActor(models.Model):
    actor = models.ForeignKey(Actor, models.DO_NOTHING, primary_key=True)
    film = models.ForeignKey(Film, models.DO_NOTHING)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "film_actor"
        unique_together = (("actor", "film"),)


class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    country = models.CharField(max_length=50)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "country"


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    city = models.CharField(max_length=50)
    country = models.ForeignKey(Country, models.DO_NOTHING)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "city"


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, blank=True, null=True)
    district = models.CharField(max_length=20)
    city = models.ForeignKey(City, models.DO_NOTHING)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "address"


class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    manager_staff_id = models.IntegerField()
    address = models.ForeignKey(Address, models.DO_NOTHING)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "store"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(Store, models.DO_NOTHING)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.CharField(max_length=50, blank=True, null=True)
    address = models.ForeignKey(Address, models.DO_NOTHING)
    active = models.BooleanField()
    create_date = models.DateField()
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "customer"


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    address = models.ForeignKey(Address, models.DO_NOTHING)
    email = models.CharField(max_length=50, blank=True, null=True)
    store = models.ForeignKey(Store, models.DO_NOTHING)
    active = models.BooleanField()
    username = models.CharField(max_length=16)
    password = models.CharField(max_length=40, blank=True, null=True)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "staff"


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    film = models.ForeignKey(Film, models.DO_NOTHING)
    store = models.ForeignKey(Store, models.DO_NOTHING)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "inventory"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    rental_date = models.DateTimeField()
    inventory = models.ForeignKey(Inventory, models.DO_NOTHING)
    customer = models.ForeignKey(Customer, models.DO_NOTHING)
    return_date = models.DateTimeField(blank=True, null=True)
    staff = models.ForeignKey(Staff, models.DO_NOTHING)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "rental"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, models.DO_NOTHING)
    staff = models.ForeignKey(Staff, models.DO_NOTHING)
    rental = models.ForeignKey(Rental, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payment"
