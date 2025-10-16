from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=150)
    nickname = models.CharField(max_length=50, blank=True, unique=True)

    def __str__(self):
        return self.nickname or self.username
