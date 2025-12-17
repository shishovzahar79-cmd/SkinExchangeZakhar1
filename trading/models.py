from django.db import models
from django.contrib.auth import get_user_model
from catalog.models import Skin

User = get_user_model()

class Order(models.Model):
    """Заявка на покупку/продажу"""
    ORDER_TYPES = [
        ('BUY', 'Покупка'),
        ('SELL', 'Продажа'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Открыта'),
        ('FILLED', 'Исполнена'),
        ('CANCELLED', 'Отменена'),
        ('PARTIAL', 'Частично исполнена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    filled_quantity = models.IntegerField(default=0)  # Сколько уже исполнено
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['skin', 'order_type', 'price', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_type} {self.skin.name} @ {self.price}"

class Transaction(models.Model):
    """Исполненная сделка"""
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bought_transactions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sold_transactions')
    skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    order_buy = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='buy_transaction')
    order_sell = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sell_transaction')
    created_at = models.DateTimeField(auto_now_add=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Комиссия
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.skin.name} x{self.quantity} @ {self.price}"