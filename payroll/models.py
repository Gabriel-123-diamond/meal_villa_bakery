from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class PayrollProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='payroll_profile')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Set a fixed monthly salary. If > 0, this will override hourly rate calculations.")

    def __str__(self):
        return f"Payroll Profile for {self.user.username}"

@receiver(post_save, sender=User)
def create_payroll_profile(sender, instance, created, **kwargs):
    if created:
        PayrollProfile.objects.create(user=instance)

class TimeClockRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.clock_in.strftime('%Y-%m-%d %H:%M')}"

    @property
    def hours_worked(self):
        if self.clock_out:
            return (self.clock_out - self.clock_in).total_seconds() / 3600
        return 0

class PayrollAdjustment(models.Model):
    ADJUSTMENT_TYPES = [('bonus', 'Bonus'), ('deduction', 'Deduction')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    reason = models.CharField(max_length=255)
    date_applied = models.DateField(auto_now_add=True)

