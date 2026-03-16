# Code Citations

## License: unknown
https://github.com/ArystanIgen/url_shortener/tree/c7f058318368352a2bffe3f4442fc7c97df9481e/src/alembic/env.py

```
= get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
```

