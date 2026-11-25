# Architecture Explanation: Digital Currency Analytics Platform

## 1. Architectural Pattern: Model-View-Template (MVT)
The application adheres to the standard Django MVT design pattern:
- **Model (`models.py`):** Represents the data layer and business entities. Maps database tables to Python objects through Django's Object-Relational Mapper (ORM).
- **View (`views.py`):** Acts as the controller. Encapsulates business logic, receives HTTP requests, interacts with models or file systems, and returns HTTP responses or rendered templates.
- **Template (`templates/`):** Presentation layer using Django Template Language (DTL) and Bootstrap for client rendering.

## 2. Component & Application Breakdown

### `digitalcurrency` (Core Project Module)
- **`settings.py`:** Configures installed applications, middleware stack, template directories, database engines, and environment-driven configurations (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`).
- **`urls.py`:** Root URL routing dispatching requests to either public landing views, `admins` views, or `users` views.
- **`views.py`:** Public landing controllers (`index`, `AdminLogin`, `UserLogin`).
- **`wsgi.py` / `asgi.py`:** WSGI/ASGI entrypoints for production web server interfaces (Gunicorn, uWSGI, Daphne).

### `admins` (Administration & Governance Module)
- **`views.py`:**
  - `AdminLoginCheck`: Handles admin authentication against environment-configured master credentials.
  - `adminhome`: Protected admin console displaying total, active, and pending accounts.
  - `RegisterUsersView`: Auditing queue displaying applicants in descending chronological order.
  - `ActivaUsers`: Protected view activating a user (`status = 'activated'`).
  - `DeleteUsers`: Protected view deleting unapproved or malicious user records.
  - `AdminLogout`: Flushes session data.
- **`tests.py`:** Unit tests verifying access control boundaries and activation flows.

### `users` (Analyst, Analytics & ML Module)
- **`models.py`:**
  - `UserRegistrationModel`: Database model storing credentials, contact info, and activation state.
- **`views.py`:**
  - `UserRegisterActions`: Handles registration form validation, uniqueness checks, and PBKDF2 hashing.
  - `UserLoginCheck`: Authenticates analysts, enforcing the `status == 'activated'` security check.
  - `UserHome`: Landing dashboard for authenticated analysts.
  - `ViewDataset`: Multi-tab CSV data viewer.
  - `training`: Executes multi-relational Pandas ETL, trains Random Forest model, and computes metrics.
  - `prediction`: Real-time inference engine computing predicted currency and probability distributions.
  - `UserLogout`: Clears user session.
- **`tests.py`:** Test suite covering password hashing, RBAC, ETL joins, model persistence, and input validation.

## 3. Communication and Data Flow
```text
HTTP Request --> Django Middleware (Security, Session, CSRF)
             --> Root URL Dispatcher (`digitalcurrency/urls.py`)
             --> View Logic (`admins/views.py` or `users/views.py`)
             --> [Optional: SQLite ORM Database Query]
             --> [Optional: Joblib ML Artifact Loading & Pandas ETL]
             --> Response Rendering (HTML + DTL Context)
             --> HTTP 200/302 Response to Client
```
