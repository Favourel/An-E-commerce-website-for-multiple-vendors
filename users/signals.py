from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from .models import Following
from users import models


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Following.objects.create(current_user=instance)
