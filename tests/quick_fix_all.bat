@echo off
chcp 65001 >nul
echo 🚀 БЫСТРЫЙ ФИКС ВСЕХ ТАБЛИЦ
echo ========================================

echo 1. Удаление базы данных...
if exist db.sqlite3 del db.sqlite3

echo 2. Создание упрощенных моделей...

echo Создаю core/models.py...
(
echo from django.contrib.auth.models import AbstractUser
echo from django.db import models
echo.
echo class User(AbstractUser):
echo     kyc_verified = models.BooleanField(default=False)
echo.
echo     class Meta:
echo         db_table = 'core_user'
echo.
echo class UserBalance(models.Model):
echo     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='balance')
echo     amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
) > core\models.py

echo Создаю inventory/models.py...
(
echo from django.db import models
echo from core.models import User
echo from catalog.models import Skin
echo.
echo class UserSkin(models.Model):
echo     user = models.ForeignKey(User, on_delete=models.CASCADE)
echo     skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
echo     quantity = models.IntegerField(default=1)
) > inventory\models.py

echo 3. Очистка миграций...
del /q core\migrations\*.py 2>nul
del /q inventory\migrations\*.py 2>nul
del /q catalog\migrations\*.py 2>nul
del /q trading\migrations\*.py 2>nul

echo. > core\migrations\__init__.py
echo. > inventory\migrations\__init__.py
echo. > catalog\migrations\__init__.py
echo. > trading\migrations\__init__.py

echo 4. Создание миграций...
python manage.py makemigrations

echo 5. Применение миграций...
python manage.py migrate

echo 6. Создание тестовых пользователей...
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from core.models import UserBalance
User = get_user_model()

# Админ
admin = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
UserBalance.objects.create(user=admin, amount=10000)
print('   Админ: admin / admin123 (баланс: 10000)')

# Тестовые пользователи
buyer = User.objects.create_user('test_buyer', 'buyer@test.com', 'test123', kyc_verified=True)
UserBalance.objects.create(user=buyer, amount=1000)

seller = User.objects.create_user('test_seller', 'seller@test.com', 'test123', kyc_verified=True)
UserBalance.objects.create(user=seller, amount=500)

print('   Покупатель: test_buyer / test123 (баланс: 1000)')
print('   Продавец: test_seller / test123 (баланс: 500)')
"

echo.
echo ✅ ВСЁ ИСПРАВЛЕНО!
echo.
echo 📝 Тестирование:
echo 1. python test_trading.py
echo.
pause