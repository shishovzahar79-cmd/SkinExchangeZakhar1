#!/usr/bin/env python
"""
Простой скрипт для исправления проблемы на Windows
"""
import os
import sys
import subprocess

print("🔧 Исправление проекта для Windows")
print("=" * 60)

# 1. Установка corsheaders
print("1. Установка django-cors-headers...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "django-cors-headers"])
    print("   ✅ Установлено")
except:
    print("   ⚠️ Не удалось установить, попробуйте вручную: pip install django-cors-headers")

# 2. Проверяем наличие manage.py
if not os.path.exists("manage.py"):
    print("❌ Файл manage.py не найден в текущей папке!")
    print(f"   Текущая папка: {os.getcwd()}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# 3. Создаем упрощенную модель inventory
print("\n2. Создание упрощенной модели inventory...")
inventory_models = """from django.db import models
from core.models import User
from catalog.models import Skin

class UserSkin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='available')
    acquired_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'skin']
    
    def __str__(self):
        return f"{self.user.username} - {self.skin.name} (x{self.quantity})"
"""

models_path = os.path.join("inventory", "models.py")
os.makedirs(os.path.dirname(models_path), exist_ok=True)

with open(models_path, "w", encoding="utf-8") as f:
    f.write(inventory_models)
print("   ✅ Модель создана")

# 4. Создаем миграции
print("\n3. Создание миграций...")
try:
    result = subprocess.run([sys.executable, "manage.py", "makemigrations", "inventory"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Миграции созданы")
        print(f"   Вывод: {result.stdout}")
    else:
        print("   ❌ Ошибка создания миграций")
        print(f"   Ошибка: {result.stderr}")
except Exception as e:
    print(f"   ❌ Исключение: {e}")

# 5. Применяем миграции
print("\n4. Применение миграций...")
try:
    result = subprocess.run([sys.executable, "manage.py", "migrate", "inventory"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Миграции применены")
        print(f"   Вывод: {result.stdout}")
    else:
        print("   ❌ Ошибка применения миграций")
        print(f"   Ошибка: {result.stderr}")
except Exception as e:
    print(f"   ❌ Исключение: {e}")

print("\n" + "=" * 60)
print("📝 Следующие шаги:")
print("1. Запустите тест: python test_windows.py")
print("2. Если тест проходит, запустите: python test_trading.py")
print("3. Если есть ошибки corsheaders, установите: pip install django-cors-headers")

input("\nНажмите Enter для завершения...")