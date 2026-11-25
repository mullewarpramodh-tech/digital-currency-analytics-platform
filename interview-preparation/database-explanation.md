# Database Design & Query Optimization

## 1. Database Schema
The primary application table is `user_registrations`, defined in `users/models.py`:

```python
class UserRegistrationModel(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(unique=True, max_length=100, db_index=True)
    password = models.CharField(max_length=128)
    mobile = models.CharField(unique=True, max_length=15)
    email = models.EmailField(unique=True, max_length=100, db_index=True)
    locality = models.CharField(max_length=100, blank=True, default='')
    address = models.TextField(max_length=1000, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=50, default='waiting', db_index=True)

    class Meta:
        db_table = 'user_registrations'
```

## 2. Key Design Decisions

### Indexing (`db_index=True`)
- `loginid`: Indexed because every user login lookup executes `SELECT ... WHERE loginid = ?`.
- `email`: Indexed for registration uniqueness validation.
- `status`: Indexed because admin dashboards frequently filter by approval state (`WHERE status = 'waiting'`).
- B-tree indexes reduce query complexity from full table scans \(O(N)\) to logarithmic lookups \(O(\log N)\).

### Password Storage (`max_length=128`)
- Django's PBKDF2 SHA-256 password hash string requires between 70 to 100 characters (`algorithm$iterations$salt$hash`).
- Expanding `max_length` to 128 prevents truncation errors while storing secure salted hashes.

### Mobile Field (`max_length=15`)
- Accommodates international telephone numbering plans (E.164 standard allows up to 15 digits) while retaining string representation to preserve leading zeros.

## 3. Query Efficiency & Django ORM Patterns
- **Existence Verification:**
  ```python
  UserRegistrationModel.objects.filter(loginid=loginid).exists()
  ```
  Generates `SELECT (1) AS a FROM user_registrations WHERE loginid = ... LIMIT 1`, which stops searching on the first match rather than loading entire model instances into memory.
- **Aggregation & Counting:**
  ```python
  UserRegistrationModel.objects.filter(status='activated').count()
  ```
  Executes an in-database `SELECT COUNT(*)` without hydrating Django model objects.
- **Safe Object Retrieval:**
  ```python
  user = get_object_or_404(UserRegistrationModel, id=user_id)
  ```
  Guarantees proper HTTP 404 response handling if an invalid ID is provided.
