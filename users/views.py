
import os
import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import render
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report


BASE_DIR = settings.BASE_DIR

def training(request):
    # Load required CSV files
    analytics_path = os.path.join(BASE_DIR, 'media', 'analytics.csv')
    wallets_path = os.path.join(BASE_DIR, 'media', 'wallets.csv')
    users_path = os.path.join(BASE_DIR, 'media', 'users.csv')

    analytics = pd.read_csv(analytics_path)
    wallets = pd.read_csv(wallets_path)
    users = pd.read_csv(users_path)

    # Add wallet_count per user from wallets.csv
    wallet_count_df = wallets.groupby("user_id").size().reset_index(name="wallet_count")
    analytics = analytics.merge(wallet_count_df, on="user_id", how="left")

    # Optionally add user feature like country (encoded)
    analytics = analytics.merge(users[["user_id", "country"]], on="user_id", how="left")
    analytics["country"] = LabelEncoder().fit_transform(analytics["country"])

    

    analytics = analytics.dropna(subset=["tx_count", "total_volume_usd", "wallet_count", "country",])
    X = analytics[["tx_count", "total_volume_usd", "wallet_count", "country"]]
    # Prepare features and label
    X = analytics[["tx_count", "total_volume_usd", "wallet_count", "country"]]
    y = analytics["most_used_currency"]
    print(analytics['most_used_currency'].value_counts())

    # Encode target
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    joblib.dump(le, os.path.join(BASE_DIR, 'media', 'currency_label_encoder.pkl'))

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(le.inverse_transform(y_test), le.inverse_transform(y_pred), output_dict=False)

    return render(request, 'users/accuracy.html', {
        'accuracy': round(acc * 100, 2),
        'report': report,
    })


def prediction(request):
    prediction_label = None
    error = None
    currency_counts = {}

    if request.method == 'POST':
        try:
            tx_count = int(request.POST['tx_count'])
            total_volume_usd = float(request.POST['total_volume_usd'])
            wallet_count = int(request.POST['wallet_count'])
            country = request.POST['country']

            # Load encoders and model
            model = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_model.pkl'))
            le = joblib.load(os.path.join(BASE_DIR, 'media', 'currency_label_encoder.pkl'))
            country_encoder = joblib.load(os.path.join(BASE_DIR, 'media', 'country_encoder.pkl'))

            if country in country_encoder.classes_:
                country_encoded = country_encoder.transform([country])[0]
            else:
                country_encoded = country_encoder.transform([country_encoder.classes_[0]])[0]

            input_data = pd.DataFrame([{
                "tx_count": tx_count,
                "total_volume_usd": total_volume_usd,
                "wallet_count": wallet_count,
                "country": country_encoded
            }])

            prediction = model.predict(input_data)[0]
            prediction_label = le.inverse_transform([prediction])[0]

        except Exception as e:
            error = str(e)

    # Always show current currency stats
    try:
        analytics_path = os.path.join(BASE_DIR, 'media', 'analytics.csv')
        analytics = pd.read_csv(analytics_path)
        currency_counts = analytics['most_used_currency'].value_counts().to_dict()
    except Exception as e:
        currency_counts = {'Error loading analytics.csv': str(e)}

    return render(request, 'users/prediction.html', {
        'prediction': prediction_label,
        'error': error,
        'currency_counts': currency_counts
    })

def ViewDataset(request):
    dataset = os.path.join(settings.MEDIA_ROOT, 'books.csv')
    import pandas as pd
    df = pd.read_csv(dataset, nrows=100)
    df = df.to_html(index=None)
    return render(request, 'users/viewData.html', {'data': df})


from django.shortcuts import render, redirect
from .models import UserRegistrationModel
from django.contrib import messages

def UserRegisterActions(request):
    if request.method == 'POST':
        user = UserRegistrationModel(
            name=request.POST['name'],
            loginid=request.POST['loginid'],
            password=request.POST['password'],
            mobile=request.POST['mobile'],
            email=request.POST['email'],
            locality=request.POST['locality'],
            address=request.POST['address'],
            city=request.POST['city'],
            state=request.POST['state'],
            status='waiting'
        )
        user.save()
        messages.success(request,"Registration successful!")
    return render(request, 'UserRegistrations.html') 


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                data = {'loginid': loginid}
                print("User id At", check.id, status)
                return render(request, 'users/UserHomePage.html', {})
            else:
                messages.success(request, 'Your Account Not at activated')
                return render(request, 'UserLogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            pass
        messages.success(request, 'Invalid Login id and password')
    return render(request, 'UserLogin.html', {})


def UserHome(request):
    return render(request, 'users/UserHomePage.html', {})


def index(request):
    return render(request,"index.html")
