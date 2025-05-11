from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    category= models.TextField()

class Car(models.Model):
    
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    image = models.FileField()
    fuel = models.TextField()
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    num_of_seats = models.IntegerField()
    price_per_day = models.IntegerField()
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return self.name
    

class Rental(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    num_days = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    advance_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_advance_paid = models.BooleanField(default=False)
    is_full_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)

    balance_due = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance_order_id = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.car.name} ({self.status})"

    @property
    def remaining_amount(self):
        return self.total_price - self.advance_paid
