Sakila ORM Data Sync
Databases Assignment 4

For a team running the MySQL Sakila OLTP database and needing a lightweight SQLite analytics warehouse fed entirely through ORM-based ETL. This project implements a Django-based pipeline that synchronizes MySQL operational data into a dimensional star-schema warehouse. All reads/writes use the Django ORM (no raw SQL except internal ORM behavior).

The system supports full-load initialization, incremental sync by timestamp, and validation routines to ensure consistency between the two databases.

---------------------------------------
Overview

Operational databases (OLTP) such as MySQL Sakila are optimized for transactions. This project builds a separate analytics database (OLAP) in SQLite using a star schema designed for reporting and aggregation.

The pipeline includes:

Dual database configuration

ORM models for MySQL source + SQLite analytics schemas

Star schema with dimensions, facts, and bridge tables

Full-load initialization

Incremental synchronization using last_update

Validation over a configurable time window

---------------------------------------
Installation

Create and activate a virtual environment

python3 -m venv .venv
source .venv/bin/activate


Install dependencies

pip install -r requirements.txt


Configure database connections (in syncproj/settings.py)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "analytics.db",
    },
    "source": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "sakila",
        "USER": "root",
        "PASSWORD": "yourpassword",
        "HOST": "localhost",
        "PORT": "3306",
    },
}


Register PyMySQL (syncapp/__init__.py):

import pymysql
pymysql.install_as_MySQLdb()

---------------------------------------
Command-Line Interface (ETL)

All ETL is implemented as Django management commands.

1. Initialize the analytics database

Creates schema, builds date dimension, initializes sync state.

python manage.py init

2. Full load (complete rebuild)

Clears and reloads the entire warehouse from source.

python manage.py full_load

3. Incremental sync

Loads only new or updated records based on timestamps.

python manage.py incremental

4. Validate (consistency checks)

Compares counts and totals over a configurable time range.

python manage.py validate
python manage.py validate --days 7


Validation includes:

Dimension table counts

Rental and payment counts

Payment revenue totals

Detection of missing rows

Analytics Schema (Star Model)

Warehouse tables include:

Dimensions
dim_date, dim_film, dim_actor, dim_category, dim_customer, dim_store

Bridges
bridge_film_actor, bridge_film_category

Facts
fact_rental, fact_payment

Metadata
sync_state

Fact tables link to dimensions using surrogate keys and date keys (YYYYMMDD).

---------------------------------------
Testing

Tests verify:

Schema initialization

Full-load correctness

Incremental insertion of new records

Incremental updates to modified records

Validation logic

FK creation in a controlled test environment

Screenshots and execution logs are provided separately.

---------------------------------------
Requirements

Python 3.11+

Django 5.x

MySQL 8.x with Sakila sample DB

SQLite (built-in)

PyMySQL