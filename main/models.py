from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_vk = models.BooleanField(default=False)
    has_tm = models.BooleanField(default=False)
    use_bot = models.BooleanField(default=False)
    tm_sesison = models.CharField(max_length=15, null=True)
