# Project Defense & Technical Interview Strategy

## 1. Why did you select this project?
**Answer:** I wanted to build an end-to-end full-stack platform that solved a realistic fintech challenge: unifying fragmented multi-relational data sources and using machine learning to derive actionable behavioral insights. This allowed me to master Django's backend architecture, database optimization, authentication security, and Scikit-Learn data science pipelines within a single coherent system.

## 2. What problem does it solve?
**Answer:** In financial and digital currency organizations, user transactional data is rarely stored in a single table. Transaction volumes live in activity ledgers, wallet balances in custodial registries, and KYC metadata in user profiles. This platform provides an automated multi-relational Pandas ETL pipeline that joins, normalizes, and feeds these disparate datasets into predictive models and interactive dashboards for analysts and administrators.

## 3. What was your specific contribution?
**Answer:**
- Designed and hardened the Django MVC architecture, URL routing, and view controllers.
- Implemented multi-tier role-based access control (RBAC), securing admin account activations and analyst session states.
- Implemented PBKDF2 SHA-256 password hashing with salting.
- Optimized database indexing (`db_index=True`) and structured safe migrations.
- Engineered the multi-relational Pandas ETL pipeline (`groupby`, joins, categorical encoding).
- Implemented the Random Forest classifier with stratified splitting, evaluation metrics, and Joblib artifact serialization.
- Authored a comprehensive 16-test automated unit and integration test suite and configured GitHub Actions CI/CD workflows.

## 4. Why did you choose Django over Flask or FastAPI?
**Answer:** Django provides an "out-of-the-box" cohesive ecosystem: an ORM with database migrations, built-in session management, CSRF protection, and a mature template engine. While Flask and FastAPI are excellent micro-frameworks for lightweight APIs, Django's integrated security features and administrative tools made it the ideal framework for a full-stack, secure financial governance and analytics platform.

## 5. How does your ML model work?
**Answer:** It uses Scikit-Learn's `RandomForestClassifier`. The model aggregates predictions from an ensemble of 100 decision trees. For each tree, a bootstrap sample of the training data is drawn, and at each decision node, a random subset of features is evaluated using Gini impurity reduction. In addition to predicting the dominant currency class, the model computes probability distributions across all five currencies via `predict_proba()`.

## 6. How is the model evaluated?
**Answer:** The dataset is split into 80% training and 20% testing sets using stratified sampling to maintain class proportions. The model is evaluated using:
- **Accuracy:** Overall percentage of correct predictions.
- **Weighted Precision, Recall, and F1-Score:** Measuring class-level classification reliability.
- **Gini Feature Importance:** Quantifying the relative contribution of each feature (Volume ~42%, Transaction count ~31%, Wallet count ~18%, Country ~9%).
- **Baseline Comparison:** Comparing against the ~20% random guess baseline for a 5-class balanced problem.

## 7. What were the main technical challenges?
**Answer:**
1. **Security Vulnerabilities in Initial Implementation:** State-changing operations were originally executed via plain GET requests and admin authentication relied on hardcoded credentials. I refactored the admin logic to use environment-based credentials and converted operations to CSRF-protected POST requests with strict session validation.
2. **Multi-Relational Data Harmonization:** Merging one-to-many wallet relationships with transaction rows required aggregation (`groupby('user_id').size()`) and left-joins that handled missing records without introducing data leakage.
3. **Handling Unseen Categorical Input in Production:** If a user enters an unobserved country during inference, a naive `LabelEncoder` would crash. I implemented defensive input validation and fallback mechanisms to ensure high availability.

## 8. What would you improve with more time?
**Answer:**
- Offload the Pandas ETL and Random Forest retraining to background asynchronous tasks using **Celery** and **Redis**.
- Connect live WebSocket price feeds (Binance or CoinGecko APIs) for real-time market data.
- Build a model registry and experiment tracking dashboard using **MLflow**.
- Upgrade from SQLite to **PostgreSQL** with connection pooling.

## 9. What are the current limitations?
**Answer:**
- The training datasets in `media/` are synthetic, exhibiting near-uniform target currency distributions, which naturally bounds accuracy close to random baseline levels (~20%).
- ML model training runs synchronously inside the Django request cycle, which is suitable for 1,000 records but would cause request timeouts on multi-million row datasets.

## 10. How would you scale the application?
**Answer:**
- **Database Layer:** Migrate to PostgreSQL, add read replicas, configure PgBouncer for connection pooling, and partition large transaction tables by date.
- **Caching Layer:** Cache frequently queried datasets and user session metadata using Redis.
- **Asynchronous Execution:** Delegate all model retraining and heavy CSV exports to Celery worker clusters.
- **Infrastructure:** Containerize with Docker and deploy across Kubernetes clusters behind Nginx reverse proxies with SSL/TLS termination and AWS S3 for media storage.
