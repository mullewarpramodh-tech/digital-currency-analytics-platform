# Technical Interview Questions & Answers

## Category 1: Python & Django Backend (20 Questions)

### Q1: What is the Model-View-Template (MVT) pattern in Django?
**Answer:** MVT is Django's architectural pattern. **Model** represents the database structure and data logic. **View** contains the business logic, handles HTTP requests, and queries models. **Template** is the presentation layer generating dynamic HTML using the Django Template Language.

### Q2: Why should you never store passwords as plaintext?
**Answer:** If the database is compromised, plaintext passwords give attackers immediate unauthorized access to user accounts. Hashing with algorithms like PBKDF2 SHA-256 uses cryptographic one-way hashing with salt, ensuring passwords cannot be reversed.

### Q3: How does Django's `make_password` and `check_password` work?
**Answer:** `make_password(password)` generates a cryptographically secure hash combining a salt, iteration count (e.g., 600,000+ iterations), and the SHA-256 algorithm. `check_password(raw_password, hashed_password)` extracts the salt from the stored hash, computes the hash for the raw password with the same parameters, and compares them using constant-time comparison to prevent timing attacks.

### Q4: What is CSRF and how does Django protect against it?
**Answer:** Cross-Site Request Forgery (CSRF) tricks a user's browser into executing unwanted actions on an authenticated application. Django protects against this using `CsrfViewMiddleware` and `{% csrf_token %}`. The server generates a unique, unpredictable secret token tied to the user's session and verifies that every state-changing POST request contains this exact token.

### Q5: Why did we replace GET requests with POST requests for user activation and deletion?
**Answer:** HTTP GET requests are designed to be idempotent and safe—they should only retrieve data without changing server state. Using GET for actions like deleting a user allows web crawlers, browser pre-fetching, or image tags (`<img src="...">`) to trigger deletions unintentionally. POST requests require explicit form submissions and CSRF tokens.

### Q6: What is the difference between `makemigrations` and `migrate`?
**Answer:** `makemigrations` inspects changes in `models.py` and creates Python migration files documenting the schema delta. `migrate` executes those migration files against the target database, applying SQL `CREATE TABLE` or `ALTER TABLE` statements inside transactions.

### Q7: Why do we use `db_index=True` on fields like `loginid` and `status`?
**Answer:** `db_index=True` instructs the database engine to build a B-tree index on that column. This speeds up lookup queries (`SELECT ... WHERE loginid = '...'`) from \(O(N)\) full table scans to \(O(\log N)\) logarithmic searches.

### Q8: What does `request.session.flush()` do during logout?
**Answer:** `flush()` deletes the current session data from the database and removes the session cookie from the client's browser, preventing session fixation or unauthorized reuse of an old session ID.

### Q9: Why is `ALLOWED_HOSTS` configured and why is `ALLOWED_HOSTS = ['*']` dangerous in production?
**Answer:** `ALLOWED_HOSTS` validates the HTTP `Host` header sent by the client. Leaving it as `['*']` exposes the application to HTTP Host Header attacks, where attackers spoof the header to poison password-reset links or cache entries.

### Q10: How does Django handle static files versus media files?
**Answer:** Static files are developer-controlled assets (CSS, JS, logos) collected during build with `collectstatic`. Media files are dynamic, user-uploaded or programmatically generated assets (CSVs, ML models) stored in `MEDIA_ROOT` and served via `MEDIA_URL`.

### Q11: What is the purpose of `get_object_or_404`?
**Answer:** It attempts to retrieve a model instance using `.get()`. If the object does not exist, instead of raising an uncaught `DoesNotExist` exception that causes a 500 Internal Server Error, it cleanly raises an `Http404` exception.

### Q12: How do you prevent SQL injection in Django?
**Answer:** Django's ORM automatically parameterizes SQL queries. When you write `UserRegistrationModel.objects.filter(loginid=user_input)`, the input is passed as a parameterized argument rather than concatenated into the SQL string.

### Q13: Why did we decouple `SECRET_KEY` into environment variables?
**Answer:** If `SECRET_KEY` is committed to version control, any attacker with repository access can forge session cookies, sign cryptographic tokens, and bypass Django authentication.

### Q14: What is the role of `STATIC_ROOT` and `STATICFILES_DIRS`?
**Answer:** `STATICFILES_DIRS` lists folders where Django looks for static assets during development. `STATIC_ROOT` is the single target directory where `python manage.py collectstatic` compiles all assets for production serving by Nginx or WhiteNoise.

### Q15: What is the difference between `.filter().exists()` and `.filter().count() > 0`?
**Answer:** `.exists()` executes `SELECT (1) ... LIMIT 1`, which terminates the search immediately upon finding the first matching row. `.count()` executes `SELECT COUNT(*)`, which continues scanning to count every matching row.

### Q16: How do you handle database transactions in Django?
**Answer:** Django provides `django.db.transaction.atomic`. Wrapping operations in an `atomic` block ensures that either all database changes succeed or, if an exception occurs, all changes roll back to maintain database consistency.

### Q17: What is Django middleware and in what order does it run?
**Answer:** Middleware is a framework of hooks into Django's request/response processing. During a request, middleware runs top-to-bottom in `settings.MIDDLEWARE`. During a response, it runs bottom-to-top.

### Q18: What is template inheritance and why is it beneficial?
**Answer:** Template inheritance allows defining a master skeleton template (e.g., `base.html`) containing common layout elements, headers, and navigation bars, with named `{% block %}` tags that child templates override. This follows the DRY (Don't Repeat Yourself) principle.

### Q19: Why should you avoid executing long-running ML training directly inside a standard Django view in production?
**Answer:** Django views run synchronously on web worker threads (like Gunicorn). A view that takes seconds or minutes to train an ML model ties up that worker, causing request queuing and timeouts for other users. In production, such tasks should be offloaded to asynchronous task queues like Celery with Redis.

### Q20: How does Django's message framework work?
**Answer:** The message framework (`django.contrib.messages`) stores temporary flash notifications in the session or cookie. They are displayed to the user on the next rendered page and automatically cleared immediately afterward.

---

## Category 2: Machine Learning & Data Processing (20 Questions)

### Q21: What is the objective of the Machine Learning pipeline in this platform?
**Answer:** To analyze behavioral indicators (transaction frequency, cumulative dollar volume, active wallet counts, and regional demographics) and predict the user's primary digital currency preference (`BTC`, `ETH`, `USDT`, `XRP`, `BNB`) with confidence probability distributions.

### Q22: What are the four features used in the model and their data sources?
**Answer:**
1. `tx_count`: Transaction frequency from `analytics.csv`.
2. `total_volume_usd`: Continuous volume from `analytics.csv`.
3. `wallet_count`: Aggregated count from `wallets.csv`.
4. `country_encoded`: Categorical encoded demographic from `users.csv`.

### Q23: Why do we use a multi-relational ETL join instead of a single flat table?
**Answer:** Real-world enterprise architectures store data in normalized tables to eliminate redundancy. Users hold multiple wallets in a 1-to-many relationship. The Pandas ETL pipeline joins and aggregates these relational tables on `user_id` to build a clean feature matrix.

### Q24: What is data leakage and how was it prevented?
**Answer:** Data leakage occurs when information from outside the training dataset (such as test set information or target-correlated identifiers) is improperly used to train the model. We prevented leakage by excluding identifiers (`user_id`, `wallet_id`), separating target `y` before splitting, and fitting encoders properly.

### Q25: Why is `stratify=y_encoded` used during `train_test_split`?
**Answer:** Stratification ensures that the train and test subsets maintain the exact same proportional distribution of target classes as the original dataset, preventing under-representation of specific currencies.

### Q26: How does the Random Forest Classifier work?
**Answer:** Random Forest is an ensemble learning method that constructs a collection of decision trees (e.g., 100 trees). Each tree is trained on a random bootstrap sample of the data, and at each split, only a random subset of features is considered. Predictions are made via majority voting across all trees.

### Q27: What is Gini Impurity?
**Answer:** Gini impurity measures the probability that a randomly chosen element from a set would be incorrectly labeled if it were randomly labeled according to the class distribution. A Gini score of 0 indicates complete node purity (all samples belong to a single class).

### Q28: How does Random Forest calculate Feature Importance?
**Answer:** Feature importance is calculated using Mean Decrease in Impurity (Gini importance). It measures the total reduction in Gini impurity brought by that feature across all split nodes in all trees in the forest.

### Q29: What was the theoretical baseline accuracy for this 5-class classification problem?
**Answer:** With 5 equally distributed target classes, a completely random guess has a baseline probability of \(1 / 5 = 20\%\). Evaluating model accuracy against this baseline helps detect whether the model has learned true underlying patterns.

### Q30: Why is accuracy alone not sufficient for evaluating classification models?
**Answer:** If a dataset has severe class imbalance (e.g., 95% Class A and 5% Class B), a naive model predicting only Class A achieves 95% accuracy while failing completely on Class B. Metrics like Precision, Recall, and F1-Score provide a more complete assessment of performance per class.

### Q31: What is the difference between Precision and Recall?
**Answer:** Precision answers: "Out of all instances predicted as Class X, how many were actually Class X?" Recall answers: "Out of all actual Class X instances, how many did the model correctly identify?"

### Q32: What is the F1-Score?
**Answer:** The F1-score is the harmonic mean of precision and recall:
\[
F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}
\]
It provides a single metric that balances both precision and recall.

### Q33: How does Joblib differ from Python's standard `pickle` for model serialization?
**Answer:** While both serialize Python objects, `joblib` is optimized for NumPy arrays and Scikit-Learn models with large numerical matrices, providing faster serialization and lower memory overhead.

### Q34: What happens if an unseen category (e.g., a new country) is passed during inference?
**Answer:** A standard `LabelEncoder.transform()` raises a `ValueError` for unseen labels. In our hardened implementation, we catch this condition and fall back safely to a default known index, preventing application crashes.

### Q35: How does `predict_proba` work in Random Forest?
**Answer:** `predict_proba` computes the fraction of individual decision trees in the forest that voted for each specific class. For example, if 45 out of 100 trees vote for `BTC`, the predicted probability for `BTC` is 45%.

### Q36: What is overfitting and how do hyperparameters control it?
**Answer:** Overfitting occurs when a model memorizes noise and idiosyncrasies of the training data rather than generalizing. In Random Forest, parameters like `max_depth` (e.g., limiting tree depth to 12) and `min_samples_split` constrain tree complexity and combat overfitting.

### Q37: What is the impact of missing values on Scikit-Learn estimators?
**Answer:** Most Scikit-Learn algorithms (including Random Forest) cannot handle `NaN` or missing values natively. Missing values must be handled during ETL via imputation (e.g., filling missing wallet counts with 0) or dropping invalid records before model fitting.

### Q38: What is the difference between supervised and unsupervised learning?
**Answer:** Supervised learning trains a model using labeled inputs and known ground-truth targets (e.g., predicting `most_used_currency` from transactional features). Unsupervised learning discovers latent patterns or groupings in unlabeled data (e.g., K-Means clustering of wallet behaviors).

### Q39: What is the curse of dimensionality?
**Answer:** As the number of feature dimensions increases, the volume of the feature space increases exponentially, making the available data sparse. This can degrade model performance and increase computational cost.

### Q40: How would you improve model accuracy if real exchange data were available?
**Answer:** By engineering richer temporal features (e.g., 7-day vs. 30-day volume moving averages, transaction frequency volatility, ratio of incoming to outgoing transfers) and tuning hyperparameters with stratified cross-validation.

---

## Category 3: Application Security, Testing & Architecture (10 Questions)

### Q41: What security vulnerabilities were identified and resolved during the audit?
**Answer:**
1. Hardcoded administrator credentials in views resolved with environment variables.
2. Insecure state-changing GET requests converted to CSRF-protected POST requests.
3. Plaintext password risks prevented with enforced PBKDF2 SHA-256 hashing.
4. Unprotected admin and user endpoints secured with session authorization checks.
5. Insecure static file warnings resolved.

### Q42: What is the purpose of automated unit testing in Django?
**Answer:** Automated tests run isolated, repeatable checks against models, views, and business logic to ensure new changes do not break existing functionality or introduce security regressions.

### Q43: How does Django's test runner handle database isolation?
**Answer:** Django creates a separate, temporary test database (e.g., `test_db.sqlite3`) at the start of the test run, executes tests inside atomic transactions that roll back after each test method, and destroys the test database upon completion.

### Q44: What is Continuous Integration (CI) and how does GitHub Actions implement it?
**Answer:** CI is the practice of automatically building and testing code on every commit or pull request. Our `.github/workflows/ci.yml` runs on Ubuntu, sets up Python 3.11, installs dependencies, runs `manage.py check`, and executes all 16 test cases to verify platform integrity before merge.

### Q45: How does session-based authentication work in Django?
**Answer:** Upon successful login, Django generates a 32-character random session key, stores the session data (e.g., `user_id`, `is_admin`) in the database (`django_session` table), and sets an HTTP-only cookie (`sessionid`) in the user's browser. On subsequent requests, Django uses this cookie to look up the session.

### Q46: Why is HTTP-only flag important for cookies?
**Answer:** The `HttpOnly` flag prevents client-side scripts (such as JavaScript) from accessing the session cookie via `document.cookie`, mitigating Session Hijacking via Cross-Site Scripting (XSS).

### Q47: What is the difference between unit tests and integration tests?
**Answer:** Unit tests verify an individual component or function in isolation (e.g., testing password hashing logic). Integration tests verify that multiple components interact correctly together (e.g., registration -> admin approval -> login -> model inference).

### Q48: How would you scale this platform to support 100,000 active users?
**Answer:**
1. Migrate from SQLite3 to PostgreSQL with read replicas and connection pooling (PgBouncer).
2. Offload ML training and heavy ETL to Celery workers backed by Redis.
3. Cache frequent queries and dataset stats using Memcached or Redis.
4. Serve static assets via AWS S3 / CloudFront CDN.
5. Deploy containerized Django instances across Kubernetes behind an Nginx load balancer.

### Q49: What is the purpose of `.env.example`?
**Answer:** It acts as a documented template of required configuration variables without revealing real secrets or credentials, enabling other developers to configure their local environments safely.

### Q50: How do you demonstrate ownership of a project in an interview?
**Answer:** By clearly explaining the architecture, the technical trade-offs made, the problems discovered during auditing, the rationale behind specific data structures or algorithms, and being honest about current limitations and future improvements.
