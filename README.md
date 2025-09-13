# CanteenKart

This project uses Flask, SQLAlchemy, and Alembic via Flask-Migrate to manage database schema migrations.

## Local development - database migrations

Install dependencies (using your preferred tool). Example with pip:

```bash
python -m pip install -r requirements.txt  # or use pyproject-based install
```

Initialize migrations (only once):

```bash
flask db init
```

Create a migration (after model changes):

```bash
flask db migrate -m "Describe changes"
```

Apply migrations to the database:

```bash
flask db upgrade
```

To revert the last migration:

```bash
flask db downgrade -1
```

## CI / Fresh setup

In CI or on a fresh environment, run:

```bash
flask db upgrade
```

This will create the database and all tables defined in the migration scripts.

## Notes

- `models/schema.sql` has been kept for reference but migrations are the source of truth.
- The app factory in `app/__init__.py` initializes Flask-Migrate. Use `flask` CLI with `FLASK_APP=app.py` to run migration commands.
