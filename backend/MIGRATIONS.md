# Migration Commands

## Create initial migration
```bash
alembic revision --autogenerate -m "Initial migration"
```

## Apply migrations
```bash
alembic upgrade head          # Apply all pending migrations
alembic upgrade +1            # Apply next migration
alembic upgrade 001_initial   # Apply specific migration
```

## Rollback migrations
```bash
alembic downgrade base        # Rollback all migrations
alembic downgrade -1          # Rollback last migration
alembic downgrade 001_initial # Rollback to specific migration
```

## View migration history
```bash
alembic history --verbose
alembic current
```

## Common scenarios

### Add new table
```bash
# 1. Modify models in app/models/
# 2. Generate migration
alembic revision --autogenerate -m "Add new_model table"
# 3. Review the migration file
# 4. Apply it
alembic upgrade head
```

### Add column to existing table
```bash
# Same process as above
alembic revision --autogenerate -m "Add column to documents"
alembic upgrade head
```

### Rename column
```bash
# Edit migration manually (autogenerate might not catch this)
alembic revision -m "Rename title to name in documents"
# Edit the migration file and use op.alter_column()
alembic upgrade head
```
