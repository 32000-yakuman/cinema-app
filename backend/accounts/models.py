from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    is_staff_member = models.BooleanField(
        default=False, help_text="窓口職員かどうか(True: 職員, False: 一般利用客)"
    )