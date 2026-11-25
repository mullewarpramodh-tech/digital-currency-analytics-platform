from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from users.models import UserRegistrationModel
import os
import pandas as pd
import joblib


class UserSecurityAndRegistrationTest(TestCase):
    """
    Validates user registration, password hashing (PBKDF2 SHA-256), and RBAC activation flow.
    """

    def setUp(self):
        self.raw_password = "SecurePassword@123"
        self.hashed = make_password(self.raw_password)
        self.user = UserRegistrationModel.objects.create(
            name="Pramodh Mullewar",
            loginid="pramodh_dev",
            password=self.hashed,
            mobile="9876543210",
            email="pramodh@example.com",
            locality="Cyberabad",
            address="Tech Corridor, Hyderabad",
            city="Hyderabad",
            state="Telangana",
            status="waiting"
        )

    def test_user_creation_and_defaults(self):
        self.assertEqual(str(self.user), "pramodh_dev")
        self.assertEqual(self.user.status, "waiting")

    def test_password_hashing_security(self):
        # Passwords must never be stored as plaintext
        self.assertNotEqual(self.user.password, self.raw_password)
        self.assertTrue(self.user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password(self.raw_password, self.user.password))
        self.assertFalse(check_password("WrongPassword", self.user.password))

    def test_duplicate_registration_validation(self):
        client = Client()
        response = client.post(reverse('UserRegisterForm'), {
            'name': 'Duplicate User',
            'loginid': 'pramodh_dev',  # duplicate loginid
            'password': 'password123',
            'mobile': '9876543211',
            'email': 'different@example.com'
        })
        self.assertEqual(response.status_code, 200)
        # Should remain only 1 user
        self.assertEqual(UserRegistrationModel.objects.filter(loginid='pramodh_dev').count(), 1)

    def test_rbac_approval_activation(self):
        self.assertEqual(self.user.status, "waiting")
        self.user.status = "activated"
        self.user.save()

        updated_user = UserRegistrationModel.objects.get(loginid="pramodh_dev")
        self.assertEqual(updated_user.status, "activated")

    def test_pending_user_cannot_login(self):
        client = Client()
        response = client.post(reverse('UserLoginCheck'), {
            'loginid': 'pramodh_dev',
            'pswd': self.raw_password
        })
        # Should stay on login page with warning message
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('loggeduser', client.session)

    def test_activated_user_can_login_and_logout(self):
        self.user.status = "activated"
        self.user.save()

        client = Client()
        response = client.post(reverse('UserLoginCheck'), {
            'loginid': 'pramodh_dev',
            'pswd': self.raw_password
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.session.get('loggeduser'), 'Pramodh Mullewar')

        # Logout test
        logout_response = client.get(reverse('UserLogout'))
        self.assertEqual(logout_response.status_code, 302)
        self.assertNotIn('loggeduser', client.session)


class MultiRelationalETLAndModelInferenceTest(TestCase):
    """
    Validates CSV dataset schemas and machine learning pipeline inference artifacts.
    """

    def setUp(self):
        self.media_dir = os.path.join(settings.BASE_DIR, 'media')
        self.analytics_csv = os.path.join(self.media_dir, 'analytics.csv')
        self.wallets_csv = os.path.join(self.media_dir, 'wallets.csv')
        self.users_csv = os.path.join(self.media_dir, 'users.csv')

    def test_dataset_files_exist(self):
        self.assertTrue(os.path.exists(self.analytics_csv), "analytics.csv must exist in media/")
        self.assertTrue(os.path.exists(self.wallets_csv), "wallets.csv must exist in media/")
        self.assertTrue(os.path.exists(self.users_csv), "users.csv must exist in media/")

    def test_multi_relational_merge(self):
        df_analytics = pd.read_csv(self.analytics_csv)
        df_wallets = pd.read_csv(self.wallets_csv)
        df_users = pd.read_csv(self.users_csv)

        self.assertIn("user_id", df_analytics.columns)
        self.assertIn("user_id", df_wallets.columns)
        self.assertIn("user_id", df_users.columns)

        wallet_count_df = df_wallets.groupby("user_id").size().reset_index(name="wallet_count")
        merged_df = df_analytics.merge(wallet_count_df, on="user_id", how="left").fillna({"wallet_count": 0})
        merged_df = merged_df.merge(df_users[["user_id", "country"]], on="user_id", how="left").fillna({"country": "Unknown"})

        self.assertGreater(len(merged_df), 0)
        self.assertIn("total_volume_usd", merged_df.columns)
        self.assertIn("wallet_count", merged_df.columns)
        self.assertIn("country", merged_df.columns)

    def test_trained_artifacts_and_inference(self):
        model_path = os.path.join(self.media_dir, 'currency_model.pkl')
        country_enc_path = os.path.join(self.media_dir, 'country_encoder.pkl')
        currency_enc_path = os.path.join(self.media_dir, 'currency_label_encoder.pkl')

        self.assertTrue(os.path.exists(model_path), "Trained Random Forest model artifact must exist")
        self.assertTrue(os.path.exists(country_enc_path), "Country label encoder artifact must exist")
        self.assertTrue(os.path.exists(currency_enc_path), "Currency label encoder artifact must exist")

        model = joblib.load(model_path)
        country_encoder = joblib.load(country_enc_path)
        currency_encoder = joblib.load(currency_enc_path)

        country_idx = int(country_encoder.transform([country_encoder.classes_[0]])[0])
        input_data = pd.DataFrame([{
            "tx_count": 15,
            "total_volume_usd": 35000.0,
            "wallet_count": 2,
            "country_encoded": country_idx
        }])

        pred_code = model.predict(input_data)[0]
        prediction_currency = currency_encoder.inverse_transform([pred_code])[0]
        self.assertIn(prediction_currency, currency_encoder.classes_)

        probs = model.predict_proba(input_data)[0]
        self.assertAlmostEqual(sum(probs), 1.0, places=4)

    def test_prediction_view_post_validation(self):
        client = Client()
        session = client.session
        session['id'] = 1
        session['loggeduser'] = 'Test User'
        session.save()

        # Valid input
        response = client.post(reverse('prediction'), {
            'tx_count': '10',
            'total_volume_usd': '15000.0',
            'wallet_count': '2',
            'country': 'USA'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('prediction', response.context)
        self.assertIsNotNone(response.context['prediction'])

        # Invalid input (negative values)
        response_invalid = client.post(reverse('prediction'), {
            'tx_count': '-5',
            'total_volume_usd': '15000.0',
            'wallet_count': '2',
            'country': 'USA'
        })
        self.assertEqual(response_invalid.status_code, 200)
        self.assertIsNotNone(response_invalid.context['error'])
