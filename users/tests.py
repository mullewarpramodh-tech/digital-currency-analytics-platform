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

    def test_rbac_approval_activation(self):
        # User starts in 'waiting' status
        self.assertEqual(self.user.status, "waiting")
        # Admin approves user
        self.user.status = "activated"
        self.user.save()

        updated_user = UserRegistrationModel.objects.get(loginid="pramodh_dev")
        self.assertEqual(updated_user.status, "activated")


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
        # Load and verify multi-relational schemas
        df_analytics = pd.read_csv(self.analytics_csv)
        df_wallets = pd.read_csv(self.wallets_csv)
        df_users = pd.read_csv(self.users_csv)

        self.assertIn("user_id", df_analytics.columns)
        self.assertIn("user_id", df_wallets.columns)
        self.assertIn("user_id", df_users.columns)

        # Replicate ETL multi-relational aggregation
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

        # Run mock inference sample
        country_code = int(country_encoder.transform([country_encoder.classes_[0]])[0])
        input_data = pd.DataFrame([{
            "tx_count": 45,
            "total_volume_usd": 12500.50,
            "wallet_count": 3,
            "country_encoded": country_code
        }])

        pred_class = model.predict(input_data)
        self.assertEqual(len(pred_class), 1)

        predicted_label = currency_encoder.inverse_transform(pred_class)[0]
        self.assertIsInstance(predicted_label, str)
        self.assertGreater(len(predicted_label), 0)

        probabilities = model.predict_proba(input_data)[0]
        confidence = float(probabilities[pred_class[0]])
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
