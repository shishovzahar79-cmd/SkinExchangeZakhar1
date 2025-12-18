#!/usr/bin/env python
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')

import django
django.setup()

from inventory.models import UserSkin

print("🔍 ПРОВЕРКА МОДЕЛИ USERSKIN")
print("=" * 60)

# 1. Показываем поля модели
print("1. Поля модели UserSkin:")
for field in UserSkin._meta.fields:
    print(f"   - {field.name}: {field.get_internal_type()}")

# 2. Показываем мета-данные
print(f"\n2. Мета-данные:")
print(f"   db_table: {UserSkin._meta.db_table}")
print(f"   unique_together: {UserSkin._meta.unique_together}")
print(f"   managed: {UserSkin._meta.managed}")

# 3. Проверяем, есть ли таблица в БД
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_userskin';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print(f"\n3. Таблица 'inventory_userskin' существует в БД")
        
        # Показываем структуру таблицы
        cursor.execute("PRAGMA table_info(inventory_userskin);")
        columns = cursor.fetchall()
        print(f"   Структура таблицы:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
    else:
        print(f"\n3. Таблица 'inventory_userskin' НЕ существует в БД")

# 4. Проверяем миграции
print(f"\n4. Проверка миграций:")
try:
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection)
    app_migrations = loader.disk_migrations.get('inventory', {})
    
    if app_migrations:
        print(f"   Миграции для 'inventory':")
        for name, migration in app_migrations.items():
            print(f"   - {name}")
    else:
        print(f"   ❌ Нет миграций для 'inventory'")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")