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
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score, f1_score

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
    if not request.session.get('id'):
        messages.warning(request, 'Please log in to access ML training and analytics.')
        return redirect('UserLogin')

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

    # Train / Test split (80/20) with stratified class distribution and fixed random seed
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Train Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))

    # Model evaluation metrics
    y_pred = model.predict(X_test)
    acc = round(accuracy_score(y_test, y_pred) * 100, 2)
    macro_precision = round(precision_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2)
    macro_recall = round(recall_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2)
    macro_f1 = round(f1_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2)

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
        'precision': macro_precision,
        'recall': macro_recall,
        'f1_score': macro_f1,
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
    if not request.session.get('id'):
        messages.warning(request, 'Please log in to access the predictive inference engine.')
        return redirect('UserLogin')

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
        available_countries = ["Canada", "Germany", "India", "UK", "USA"]

    if request.method == 'POST':
        try:
            raw_tx = request.POST.get('tx_count', '').strip()
            raw_vol = request.POST.get('total_volume_usd', '').strip()
            raw_wallets = request.POST.get('wallet_count', '').strip()
            country = request.POST.get('country', '').strip()

            # Strict input validation
            if not raw_tx or not raw_vol or not raw_wallets or not country:
                raise ValueError("All inference parameters (transactions, volume, wallets, and country) are required.")

            tx_count = int(raw_tx)
            total_volume_usd = float(raw_vol)
            wallet_count = int(raw_wallets)

            if tx_count < 0 or tx_count > 100000:
                raise ValueError("Transaction count must be a non-negative integer under 100,000.")
            if total_volume_usd < 0.0 or total_volume_usd > 1000000000.0:
                raise ValueError("Total volume (USD) must be a non-negative amount.")
            if wallet_count < 0 or wallet_count > 100:
                raise ValueError("Wallet count must be an integer between 0 and 100.")

            # Load trained artifacts
            model = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))
            currency_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_label_encoder.pkl'))
            country_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'country_encoder.pkl'))

            # Safely handle unseen country categories
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
            error = f"Inference parameter validation error: {str(e)}"

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
    if not request.session.get('id'):
        messages.warning(request, 'Please log in to view platform datasets.')
        return redirect('UserLogin')

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

    return render(request, 'users/viewData.html', {
        'data': table_html,
        'dataset_type': dataset_type,
        'display_title': display_title,
        'total_rows': total_rows,
        'total_cols': total_cols
    })


def UserRegisterActions(request):
    """
    User registration with input validation and secure PBKDF2 password hashing.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        loginid = request.POST.get('loginid', '').strip()
        raw_password = request.POST.get('password', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        locality = request.POST.get('locality', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()

        # Input validation
        if not name or not loginid or not raw_password or not mobile or not email:
            messages.error(request, "Name, Login ID, Password, Mobile, and Email are required fields.")
            return render(request, 'UserRegistrations.html')

        if len(raw_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'UserRegistrations.html')

        if UserRegistrationModel.objects.filter(loginid=loginid).exists():
            messages.error(request, f"Login ID '{loginid}' is already registered. Please choose another.")
            return render(request, 'UserRegistrations.html')

        if UserRegistrationModel.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return render(request, 'UserRegistrations.html')

        if UserRegistrationModel.objects.filter(mobile=mobile).exists():
            messages.error(request, f"Mobile number '{mobile}' is already registered.")
            return render(request, 'UserRegistrations.html')

        hashed_password = make_password(raw_password)

        user = UserRegistrationModel(
            name=name,
            loginid=loginid,
            password=hashed_password,
            mobile=mobile,
            email=email,
            locality=locality,
            address=address,
            city=city,
            state=state,
            status='waiting'
        )
        user.save()
        messages.success(request, "Registration successful! Your account is pending admin activation.")
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
            # Verify password using Django PBKDF2 hasher
            if check_password(pswd, user.password):
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
    if not request.session.get('id'):
        messages.warning(request, 'Please log in to access the user dashboard.')
        return redirect('UserLogin')
    return render(request, 'users/UserHomePage.html', {
        'loggeduser': request.session.get('loggeduser', 'User')
    })


def UserLogout(request):
    """Logs out analyst user and clears session."""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('UserLogin')


def index(request):
    return render(request, "index.html")
