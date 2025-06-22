from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    class Role(models.TextChoices):
        STAFF = 'staff', 'Staff'
        SUPERVISOR = 'supervisor', 'Supervisor'
        MANAGER = 'manager', 'Manager'
        BAKER = 'baker', 'Baker'
        CLEANER = 'cleaner', 'Cleaner'
        ACCOUNTANT = 'accountant', 'Accountant'
        STOREKEEPER = 'storekeeper', 'Storekeeper'
        DEVELOPER = 'developer', 'Developer'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    staff_id = models.CharField(max_length=10, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not instance.profile.staff_id:
        instance.profile.staff_id = instance.username
    instance.profile.save()

