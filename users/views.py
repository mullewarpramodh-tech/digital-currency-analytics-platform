import os
import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

from .models import UserRegistrationModel

BASE_DIR = settings.BASE_DIR


def training(request):
    """
    Multi-relational data pipeline & Scikit-Learn Random Forest training.
    Merges:
      1. media/analytics.csv (tx_count, total_volume_usd, most_used_currency)
      2. media/wallets.csv (aggregated wallet_count per user)
      3. media/users.csv (demographic country feature)
    Persists:
      - currency_model.pkl
      - currency_label_encoder.pkl
      - country_encoder.pkl
    """
    analytics_path = os.path.join(BASE_DIR, 'media', 'analytics.csv')
    wallets_path = os.path.join(BASE_DIR, 'media', 'wallets.csv')
    users_path = os.path.join(BASE_DIR, 'media', 'users.csv')

    analytics = pd.read_csv(analytics_path)
    wallets = pd.read_csv(wallets_path)
    users = pd.read_csv(users_path)

    # Multi-relational join 1: wallet count per user
    wallet_count_df = wallets.groupby("user_id").size().reset_index(name="wallet_count")
    analytics = analytics.merge(wallet_count_df, on="user_id", how="left").fillna({"wallet_count": 0})

    # Multi-relational join 2: demographic country per user
    analytics = analytics.merge(users[["user_id", "country"]], on="user_id", how="left").fillna({"country": "Unknown"})

    # Clean missing values
    analytics = analytics.dropna(subset=["tx_count", "total_volume_usd", "wallet_count", "country", "most_used_currency"])

    # Categorical feature encoding for Country
    country_encoder = LabelEncoder()
    analytics["country_encoded"] = country_encoder.fit_transform(analytics["country"].astype(str))
    joblib.dump(country_encoder, os.path.join(BASE_DIR, 'media', 'country_encoder.pkl'))

    # Feature matrix X and Target vector y
    feature_cols = ["tx_count", "total_volume_usd", "wallet_count", "country_encoded"]
    X = analytics[feature_cols]
    y = analytics["most_used_currency"]

    # Target label encoding for currencies (e.g. BTC, ETH, USDT, XRP, BNB)
    currency_encoder = LabelEncoder()
    y_encoded = currency_encoder.fit_transform(y)
    joblib.dump(currency_encoder, os.path.join(BASE_DIR, 'media', 'currency_label_encoder.pkl'))

    # Train / Test split (80/20) with reproducible seed
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Train Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))

    # Model evaluation
    y_pred = model.predict(X_test)
    acc = round(accuracy_score(y_test, y_pred) * 100, 2)
    report_text = classification_report(
        currency_encoder.inverse_transform(y_test),
        currency_encoder.inverse_transform(y_pred),
        output_dict=False
    )

    # Feature importances breakdown
    feature_display_names = ["Transaction Count", "Total Volume (USD)", "Wallet Count", "Country Demographics"]
    feature_importances = [
        {"name": name, "importance": round(imp * 100, 2)}
        for name, imp in zip(feature_display_names, model.feature_importances_)
    ]
    feature_importances.sort(key=lambda x: x["importance"], reverse=True)

    return render(request, 'users/accuracy.html', {
        'accuracy': acc,
        'report': report_text,
        'feature_importances': feature_importances,
        'total_samples': len(analytics),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'classes': list(currency_encoder.classes_)
    })


def prediction(request):
    """
    On-demand predictive classification and probability scoring for digital currency adoption.
    """
    prediction_label = None
    currency_probabilities = {}
    error = None
    currency_counts = {}
    available_countries = []

    # Load country encoder classes for dropdown selection
    try:
        country_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'country_encoder.pkl'))
        available_countries = sorted(list(country_encoder.classes_))
    except Exception:
        available_countries = ["USA", "UK", "Germany", "Canada", "India", "Australia"]

    if request.method == 'POST':
        try:
            tx_count = int(request.POST.get('tx_count', 0))
            total_volume_usd = float(request.POST.get('total_volume_usd', 0.0))
            wallet_count = int(request.POST.get('wallet_count', 1))
            country = request.POST.get('country', '').strip()

            # Load trained artifacts
            model = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))
            currency_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_label_encoder.pkl'))
            country_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'country_encoder.pkl'))

            # Safely encode country input
            if country in country_encoder.classes_:
                country_encoded = int(country_encoder.transform([country])[0])
            else:
                country_encoded = int(country_encoder.transform([country_encoder.classes_[0]])[0])

            input_data = pd.DataFrame([{
                "tx_count": tx_count,
                "total_volume_usd": total_volume_usd,
                "wallet_count": wallet_count,
                "country_encoded": country_encoded
            }])

            # Predict target class
            pred_code = model.predict(input_data)[0]
            prediction_label = currency_encoder.inverse_transform([pred_code])[0]

            # Compute probability distribution across all currencies
            probs = model.predict_proba(input_data)[0]
            currency_probabilities = {
                curr: round(float(prob) * 100, 2)
                for curr, prob in zip(currency_encoder.classes_, probs)
            }
            currency_probabilities = dict(sorted(currency_probabilities.items(), key=lambda item: item[1], reverse=True))

        except Exception as e:
            error = f"Inference exception: {str(e)}"

    # Load dataset distribution summary
    try:
        analytics_path = os.path.join(BASE_DIR, 'media', 'analytics.csv')
        analytics = pd.read_csv(analytics_path)
        currency_counts = analytics['most_used_currency'].value_counts().to_dict()
    except Exception as e:
        currency_counts = {'Error': str(e)}

    return render(request, 'users/prediction.html', {
        'prediction': prediction_label,
        'currency_probabilities': currency_probabilities,
        'error': error,
        'currency_counts': currency_counts,
        'available_countries': available_countries
    })


def ViewDataset(request):
    """
    Multi-relational dataset browser (analytics.csv, wallets.csv, users.csv).
    """
    dataset_type = request.GET.get('dataset', 'analytics')
    valid_files = {
        'analytics': ('analytics.csv', 'Transaction Analytics Dataset'),
        'wallets': ('wallets.csv', 'Multi-Currency Wallets Dataset'),
        'users': ('users.csv', 'Demographic User Profiles Dataset')
    }

    filename, display_title = valid_files.get(dataset_type, ('analytics.csv', 'Transaction Analytics Dataset'))
    filepath = os.path.join(BASE_DIR, 'media', filename)

    try:
        df = pd.read_csv(filepath)
        total_rows = len(df)
        total_cols = len(df.columns)
        table_html = df.head(50).to_html(classes="table table-striped table-hover table-bordered", index=False)
    except Exception as e:
        total_rows = 0
        total_cols = 0
        table_html = f"<div class='alert alert-danger'>Error loading dataset: {str(e)}</div>"

    return render(request, 'users/viewData.html', {
        'data': table_html,
        'dataset_type': dataset_type,
        'display_title': display_title,
        'total_rows': total_rows,
        'total_cols': total_cols
    })


def UserRegisterActions(request):
    """
    User registration with secure PBKDF2 password hashing.
    """
    if request.method == 'POST':
        raw_password = request.POST.get('password', '')
        hashed_password = make_password(raw_password)

        user = UserRegistrationModel(
            name=request.POST.get('name', ''),
            loginid=request.POST.get('loginid', ''),
            password=hashed_password,
            mobile=request.POST.get('mobile', ''),
            email=request.POST.get('email', ''),
            locality=request.POST.get('locality', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            status='waiting'
        )
        user.save()
        messages.success(request, "Registration successful! Awaiting admin activation.")
        return redirect('UserLogin')

    return render(request, 'UserRegistrations.html')


def UserLoginCheck(request):
    """
    User authentication supporting hashed and legacy passwords.
    """
    if request.method == "POST":
        loginid = request.POST.get('loginid', '')
        pswd = request.POST.get('pswd', '')

        try:
            user = UserRegistrationModel.objects.get(loginid=loginid)
            # Verify password (supports hashed and plaintext migration)
            password_matches = check_password(pswd, user.password) or (user.password == pswd)

            if password_matches:
                if user.status == "activated":
                    request.session['id'] = user.id
                    request.session['loggeduser'] = user.name
                    request.session['loginid'] = user.loginid
                    request.session['email'] = user.email
                    return redirect('UserHome')
                else:
                    messages.warning(request, 'Your account is pending admin activation.')
                    return render(request, 'UserLogin.html')
            else:
                messages.error(request, 'Invalid credentials.')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')

    return render(request, 'UserLogin.html', {})


def UserHome(request):
    return render(request, 'users/UserHomePage.html', {
        'loggeduser': request.session.get('loggeduser', 'User')
    })


def index(request):
    return render(request, "index.html")
