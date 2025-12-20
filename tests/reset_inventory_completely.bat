@echo off
chcp 65001 >nul
echo 🗑️ ПОЛНЫЙ СБРОС МИГРАЦИЙ INVENTORY
echo ========================================

echo 1. Удаление файлов миграций...
if exist inventory\migrations\*.py del inventory\migrations\*.py

echo 2. Удаление кэша миграций...
if exist inventory\migrations\__pycache__ rmdir /s /q inventory\migrations\__pycache__

echo 3. Создание чистого __init__.py...
echo. > inventory\migrations\__init__.py

echo 4. Удаление записей из базы данных...
python -c "
import sqlite3
try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute(\"DELETE FROM django_migrations WHERE app = 'inventory'\")
    cursor.execute(\"DROP TABLE IF EXISTS inventory_userskin\")
    conn.commit()
    print('   ✅ Таблица и записи удалены из БД')
except Exception as e:
    print(f'   ⚠️ Ошибка: {e}')
finally:
    conn.close()
"

echo 5. Создание чистой модели...
(
echo from django.db import models
echo from core.models import User
echo from catalog.models import Skin
echo.
echo class UserSkin(models.Model):
echo     '''Упрощенная модель для тестирования'''
echo     user = models.ForeignKey(User, on_delete=models.CASCADE)
echo     skin = models.ForeignKey(Skin, on_delete=models.CASCADE)
echo     quantity = models.IntegerField(default=1)
echo     status = models.CharField(max_length=20, default='available')
echo     acquired_date = models.DateTimeField(auto_now_add=True)
echo.
echo     class Meta:
echo         db_table = 'inventory_userskin'
echo         unique_together = ['user', 'skin']
echo.
echo     def __str__(self):
echo         return f'{self.user.username} - {self.skin.name} (x{self.quantity})'
) > inventory\models.py

echo 6. Создание новой миграции...
python manage.py makemigrations inventory --name initial

echo 7. Применение миграции...
python manage.py migrate inventory

echo.
echo ✅ ПОЛНЫЙ СБРОС ВЫПОЛНЕН!
echo.
echo 📝 Для проверки запустите:
echo python test_simple_after_reset.py
echo.
pause