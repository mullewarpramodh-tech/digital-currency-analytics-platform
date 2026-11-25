from django.db import models


class UserRegistrationModel(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(unique=True, max_length=100, db_index=True)
    password = models.CharField(max_length=128)
    mobile = models.CharField(unique=True, max_length=15)
    email = models.EmailField(unique=True, max_length=100, db_index=True)
    locality = models.CharField(max_length=100, blank=True, default='')
    address = models.TextField(max_length=1000, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=50, default='waiting', db_index=True)

    def __str__(self):
        return self.loginid

    class Meta:
        db_table = 'user_registrations'

