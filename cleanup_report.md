# Cleanup report

The following files were removed because they were standalone reference notes and are not referenced anywhere in the project configuration or code:

- `config_overrides.txt`
- `django_cheatsheet.txt`
- `docs/i18n_refactor_guide.md`

Items that remain and appear required:

- `db_setup/init.sql` is mounted by `docker-compose.yml` for PostgreSQL initialization.
- `.env.example` is referenced in the setup instructions in `README.md`.
