# Django Framework Explanation

## 1. Django URLs & Routing
Django uses a declarative URL routing system defined in `urlpatterns`:
```python
path('prediction/', usr.prediction, name='prediction')
```
- **Path function:** Associates an exact URL string with a Python callable view.
- **Name argument:** Assigns a reverse-lookup identifier. Templates use `{% url 'prediction' %}` instead of hardcoded paths, making URL restructuring effortless.

## 2. Views and Request-Response Cycle
Every view is a Python function that takes an `HttpRequest` object and returns an `HttpResponse`:
- **Session verification:**
  ```python
  if not request.session.get('id'):
      return redirect('UserLogin')
  ```
- **HTTP method segregation:** Checking `request.method == 'POST'` to separate form submission logic from GET page rendering.
- **Context dictionary:** Passes dynamic backend variables to templates:
  ```python
  return render(request, 'users/accuracy.html', {'accuracy': acc, 'classes': classes})
  ```

## 3. Django Models & ORM (Object-Relational Mapping)
The Django ORM bridges Python code and SQL database tables:
- **Field Definitions:** `CharField`, `EmailField`, `TextField`.
- **Database Indexing:** `db_index=True` creates B-tree indexes on columns frequently filtered or queried (`loginid`, `email`, `status`).
- **QuerySet API:**
  - `UserRegistrationModel.objects.filter(status='waiting')` generates `SELECT ... WHERE status = 'waiting'`.
  - `UserRegistrationModel.objects.count()` generates `SELECT COUNT(*) FROM user_registrations`.
  - `.order_by('-id')` generates `ORDER BY id DESC`.

## 4. Database Migrations
Migrations are Django's way of propagating changes made to models into the database schema:
- `python manage.py makemigrations`: Inspects `models.py` and creates migration scripts (`0001_initial.py`, `0002_alter_...py`).
- `python manage.py migrate`: Executes DDL statements inside an atomic transaction against SQLite3.

## 5. Middleware Stack
Middleware components process requests and responses globally:
- `SecurityMiddleware`: Configures security headers.
- `SessionMiddleware`: Manages session cookies and storage across requests.
- `CommonMiddleware`: Handles URL normalization and header checks.
- `CsrfViewMiddleware`: Validates CSRF tokens on incoming POST requests to prevent cross-site request forgery.
- `AuthenticationMiddleware`: Associates users with requests using sessions.
- `MessageMiddleware`: Handles one-time flash notifications (`messages.success`, `messages.error`).

## 6. Template Engine & Inheritance
Templates utilize layout inheritance via `{% extends 'base.html' %}` and `{% block contents %}`:
- Prevents redundant HTML boilerplate.
- Provides unified headers, footers, and Bootstrap CDN links.
- Uses filters such as `{{ accuracy }}%` and tags such as `{% for user in data %}`.
