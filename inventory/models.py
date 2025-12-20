from django.db import models
from core.models import User
from catalog.models import Skin

class UserSkin(models.Model):
    """Скин пользователя - упрощенная версия"""
    
    # Убираем сложные choices для простоты
    STATUS_AVAILABLE = 'available'
    STATUS_IN_TRADE = 'in_trade'
    STATUS_SOLD = 'sold'
    
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Доступен'),
        (STATUS_IN_TRADE, 'В обмене'),
        (STATUS_SOLD, 'Продан'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    acquired_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_userskin'
        unique_together = ['user', 'skin']
    
    def __str__(self):
        return f"{self.user.username} - {self.skin.name} (x{self.quantity})"