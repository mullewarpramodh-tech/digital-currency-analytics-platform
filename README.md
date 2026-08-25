# Unified Digital Currency Management & Analytics Platform

An enterprise-grade, full-stack web application built with **Django** designed to analyze transaction metrics and predict digital currency usage behavior using **Machine Learning**. 

The system enables users and administrators to securely manage, train, and leverage predictive models based on real-world transaction patterns.

## 🚀 Key Features

*   **User & Admin Authentication:** Multi-tier access control system. Admins retain strict control to review, activate, or deactivate registered users before granting dashboard access.
*   **Machine Learning Pipeline:** A robust predictive backend powered by **Scikit-Learn**. Features are extracted and engineered from multiple relational datasets (users, wallets, and transactions) using **Pandas**. The pipeline merges demographic details (country), transaction counts, total transaction volume (USD), and user wallet counts.
*   **Predictive Model (Random Forest):** Dynamically trains a Random Forest Classifier to identify and predict a user's most frequently utilized digital currency. The interface displays real-time accuracy and classification reports (precision, recall, f1-score).
*   **Interactive Analytics Interface:** A dedicated prediction dashboard where users can input transaction counts, USD volumes, wallet quantities, and country profiles to run predictive classification models on-demand.
*   **Data Visibility & Auditing:** Provides administrative capabilities to seamlessly audit user details and review database records.

## 🛠️ Tech Stack

*   **Backend Framework:** Python, Django
*   **Machine Learning:** Scikit-Learn (Random Forest Classifier), Pandas, NumPy, Joblib
*   **Database:** SQLite
*   **Frontend:** HTML5, CSS3, Bootstrap

## ⚙️ Architecture Flow

1.  **Data Ingestion:** Relational data containing user demographics and transaction history is processed via Pandas DataFrames.
2.  **Feature Engineering:** Critical predictive metrics (e.g., volume, wallet count) are isolated.
3.  **Model Training:** The Random Forest model is trained or updated.
4.  **Web Interface:** Django serves the trained model via a secure, authenticated REST-like interface, allowing end-users to input new mock data and receive instant currency predictions.
