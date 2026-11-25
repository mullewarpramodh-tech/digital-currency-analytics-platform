# Machine Learning Pipeline Explanation

## 1. Datasets and Ingestion
The platform operates on three distinct datasets in `media/`:
1. `analytics.csv` (1,000 records): Contains transaction telemetry (`user_id`, `date`, `tx_count`, `total_volume_usd`, `most_used_currency`).
2. `wallets.csv` (6,000 records): Contains individual wallet records (`wallet_id`, `user_id`, `currency`, `balance`, `wallet_address`).
3. `users.csv` (4,000 records): Contains user demographic information (`user_id`, `name`, `email`, `country`, `account_created`).

## 2. Multi-Relational ETL & Feature Engineering
Rather than training directly on raw single-table rows, the ETL pipeline merges heterogeneous data sources:
```python
# 1. Relational aggregation: Count distinct wallets owned by each user
wallet_count_df = wallets.groupby("user_id").size().reset_index(name="wallet_count")
analytics = analytics.merge(wallet_count_df, on="user_id", how="left").fillna({"wallet_count": 0})

# 2. Demographic enrichment: Merge country metadata
analytics = analytics.merge(users[["user_id", "country"]], on="user_id", how="left").fillna({"country": "Unknown"})

# 3. Clean missing records
analytics = analytics.dropna(subset=["tx_count", "total_volume_usd", "wallet_count", "country", "most_used_currency"])
```

## 3. Categorical Encoding & Preventing Leakage
- **Feature Encoding (`country`):** Transformed via Scikit-Learn's `LabelEncoder`. The encoder is serialized to `media/country_encoder.pkl`. During inference, unseen country categories fall back safely to a default known index instead of raising runtime exceptions.
- **Target Encoding (`most_used_currency`):** The 5 multi-class labels (`BTC`, `ETH`, `USDT`, `XRP`, `BNB`) are encoded into integer codes `[0, 1, 2, 3, 4]` and serialized to `media/currency_label_encoder.pkl`.

## 4. Train/Test Split & Stratification
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
```
- **Stratification:** Preserves equal proportional representation of each currency across both train and test splits, eliminating sampling bias.
- **Reproducibility:** A fixed random seed (`random_state=42`) ensures identical split boundaries across executions.

## 5. Model Architecture: Random Forest Classifier
```python
model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
model.fit(X_train, y_train)
```
- **Algorithm:** Ensemble of 100 decision trees using bootstrap aggregating (bagging) and random feature subspace selection.
- **Why Random Forest:** Non-linear decision boundaries, robustness against outliers, built-in feature importance estimation, and resistance to overfitting compared to single decision trees.

## 6. Evaluation Metrics & Telemetry
- **Accuracy:** Overall percentage of correct predictions.
- **Precision:** `TP / (TP + FP)` - Measures accuracy of positive class assignments.
- **Recall:** `TP / (TP + FN)` - Measures coverage of actual class instances.
- **F1-Score:** Harmonic mean of precision and recall.
- **Baseline Understanding:** With 5 equally distributed target classes (~20% each), a completely random baseline yields 20% accuracy. The project evaluates model performance against this theoretical baseline.

## 7. Model Persistence & Inference Flow
- **Joblib Serialization:** Saves the model object graph into binary format.
- **Inference Execution:**
  ```python
  model = joblib.load('media/currency_model.pkl')
  pred_code = model.predict(input_data)[0]
  probabilities = model.predict_proba(input_data)[0]
  ```
- Predicts both the most likely currency class and the relative probability distribution across all 5 assets.
