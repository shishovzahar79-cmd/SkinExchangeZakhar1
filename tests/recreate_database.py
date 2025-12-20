#!/usr/bin/env python
"""
Пересоздание базы данных с сохранением данных (опционально)
"""
import os
import sqlite3
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_DB = os.path.join(BASE_DIR, 'db.sqlite3')
BACKUP_DB = os.path.join(BASE_DIR, 'db_backup.sqlite3')
NEW_DB = os.path.join(BASE_DIR, 'db_new.sqlite3')

print("🔄 ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ")
print("=" * 60)

# 1. Создаем резервную копию
if os.path.exists(OLD_DB):
    shutil.copy2(OLD_DB, BACKUP_DB)
    print(f"✅ Резервная копия создана: {BACKUP_DB}")
    
    # Показываем размер старой БД
    size_mb = os.path.getsize(OLD_DB) / 1024 / 1024
    print(f"   Размер старой БД: {size_mb:.2f} MB")
else:
    print("⚠️ Старая база данных не найдена")

# 2. Удаляем старую базу
if os.path.exists(OLD_DB):
    os.remove(OLD_DB)
    print("✅ Старая база данных удалена")

# 3. Проверяем наличие папки migrations
migrations_dirs = ['core/migrations', 'inventory/migrations', 
                   'catalog/migrations', 'trading/migrations']

print("\n📁 Проверка папок migrations:")
for dir_path in migrations_dirs:
    full_path = os.path.join(BASE_DIR, dir_path)
    if os.path.exists(full_path):
        py_files = [f for f in os.listdir(full_path) if f.endswith('.py') and f != '__init__.py']
        print(f"   {dir_path}: {len(py_files)} файлов миграций")
    else:
        print(f"   ❌ {dir_path} не существует")

# 4. Создаем новую базу через Django
print("\n🚀 Создание новой базы данных...")
try:
    # Запускаем миграции
    print("1. Создание миграций...")
    os.system('python manage.py makemigrations')
    
    print("2. Применение миграций...")
    os.system('python manage.py migrate')
    
    print("3. Проверка новой базы...")
    if os.path.exists(OLD_DB):
        new_size = os.path.getsize(OLD_DB)
        print(f"   ✅ Новая база создана: {new_size} байт")
        
        # Показываем таблицы
        conn = sqlite3.connect(OLD_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"   Создано таблиц: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("   ❌ Новая база не создана")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")

# 5. Создаем суперпользователя
print("\n👑 Создание администратора...")
try:
    os.system('python manage.py createsuperuser --username admin --email admin@test.com --noinput')
    
    # Устанавливаем пароль
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("✅ Администратор создан: admin / admin123")
    
except Exception as e:
    print(f"⚠️ Не удалось создать администратора: {e}")
    print("   Создайте вручную: python manage.py createsuperuser")

print("\n" + "=" * 60)
print("📝 ИТОГ:")
print(f"1. Старая БД: {BACKUP_DB if os.path.exists(BACKUP_DB) else 'не сохранена'}")
print(f"2. Новая БД: {OLD_DB if os.path.exists(OLD_DB) else 'не создана'}")
print("3. Для восстановления данных из backup запустите: python restore_data.py")

input("\nНажмите Enter для завершения...")