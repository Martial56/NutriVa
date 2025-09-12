# NutriVa AI Coding Agent Instructions

## Project Overview
NutriVa is a Django-based web application focused on patient management and nutrition tracking. The codebase is organized into Django's standard structure, with the main project in `NutriVa/` and a core app in `patient/`.

## Architecture & Major Components
- **NutriVa/**: Django project settings, URLs, and WSGI/ASGI entry points.
- **patient/**: Main Django app for patient management. Contains models, views, URLs, templates, static files, and migrations.
- **Templates**: Located in `patient/templates/patient/`, used for rendering patient-related pages.
- **Static Files**: Located in `patient/static/`, includes images and CSS for patient UI.
- **Database**: Uses SQLite (`db.sqlite3`) by default.

## Developer Workflows
- **Run Server**: `python manage.py runserver` (from project root)
- **Migrations**: `python manage.py makemigrations patient` then `python manage.py migrate`
- **Tests**: `python manage.py test patient`
- **Admin**: Django admin is enabled via `patient/admin.py` and configured in `NutriVa/settings.py`.

## Project-Specific Patterns
- **App Structure**: All patient logic is in the `patient` app. Follow Django conventions for models, views, and templates.
- **Templates**: Use `{% extends %}` and `{% block %}` for template inheritance. Patient pages are in `patient/templates/patient/`.
- **Static Files**: Reference static assets using `{% load static %}` and `{% static 'patient/style.css' %}`.
- **URLs**: Project-level URLs in `NutriVa/urls.py`, app-level in `patient/urls.py`. Include app URLs in project URLs.
- **Migrations**: All schema changes go through Django migrations in `patient/migrations/`.

## Integration Points
- **No external APIs or custom middleware detected.**
- **All business logic is handled in Django views and models.**

## Examples
- To add a new patient model field: edit `patient/models.py`, run migrations, update forms/views/templates as needed.
- To add a new page: create a template in `patient/templates/patient/`, add a view in `patient/views.py`, and map it in `patient/urls.py`.

## Key Files
- `NutriVa/settings.py`: Project configuration
- `NutriVa/urls.py`: Main URL routing
- `patient/models.py`: Patient data models
- `patient/views.py`: Business logic and page rendering
- `patient/templates/patient/`: HTML templates
- `patient/static/patient/style.css`: Main CSS

## Conventions
- Follow Django's best practices for app structure, migrations, and template usage.
- Keep patient-related logic within the `patient` app.
- Use relative imports within apps.

---
**If any section is unclear or missing, please provide feedback for further refinement.**
