# Project Overview: Digital Currency Analytics Platform

## 1. Executive Summary
The **Unified Digital Currency Management & Analytics Platform** is a full-stack Python/Django web application engineered to ingest, merge, and analyze distributed cryptocurrency and wallet telemetry. It integrates a multi-relational Pandas ETL pipeline, an ensemble Random Forest predictive classifier, role-based access control (RBAC), and an interactive analytics dashboard.

## 2. Business Problem & Motivation
In decentralized finance (DeFi) and modern digital currency exchanges, operational data is fragmented across separate domains:
- **Transaction ledgers:** Containing volume, frequencies, and preferred assets.
- **Wallet balances:** Holding multi-currency addresses, tokens, and active custodial balances.
- **Demographics:** Containing user location, registration dates, and KYC details.

Without unifying these silos, exchanges and analytics firms cannot segment users effectively or predict customer adoption patterns. This platform solves that challenge by merging heterogeneous relational tables into an unified analytical feature store and training machine learning algorithms to predict customer asset preferences.

## 3. High-Level Architecture
The system follows the Django Model-View-Template (MVT) pattern augmented with an integrated data science pipeline:
- **Presentation Layer (Templates):** Responsive Bootstrap 4/5 interfaces with custom styling for both user and administrative workspaces.
- **Application Controller Layer (Views):** Python views handling request parsing, authentication checks, dataset serving, model retraining, and real-time inference.
- **Data Persistence Layer (Django ORM & Models):** SQLite3 database with optimized indexes for user authentication, auditing, and status flags.
- **Analytics & ML Engine:** Pandas ETL merging `analytics.csv`, `wallets.csv`, and `users.csv`, paired with Scikit-Learn Random Forest estimators serialized using Joblib.

## 4. Key Workflows
1. **Analyst Registration & Onboarding:**
   - User registers via `UserRegistrations.html`.
   - Password is encrypted using PBKDF2 SHA-256.
   - Account is assigned status `waiting` and blocked from accessing analytics until reviewed.
2. **Administrative Auditing & RBAC Approval:**
   - Admin logs into `/Adminlogin`.
   - Admin inspects applicant list at `/userDetails`.
   - Admin clicks 'Activate' or 'Delete' (protected by POST and CSRF).
3. **Multi-Relational Data Ingestion & Exploration:**
   - Authenticated user navigates to `/ViewDataset/` to browse transactions, wallet counts, and demographics.
4. **Model Retraining & Telemetry:**
   - Authenticated user triggers `/training`.
   - Pipeline dynamically extracts wallet counts per user (`groupby`), joins with demographics, encodes categories, performs stratified 80/20 train/test split, fits Random Forest, and renders evaluation telemetry.
5. **Real-Time On-Demand Inference:**
   - User inputs transaction velocity, cumulative volume, wallet count, and country at `/prediction/`.
   - Backend loads serialized model and encoders, generates class predictions, and computes multi-class probability distributions.
