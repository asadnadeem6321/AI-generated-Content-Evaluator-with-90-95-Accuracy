from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    # agar custom fields chahiye to yahan add karo
    name = models.CharField()
    pass