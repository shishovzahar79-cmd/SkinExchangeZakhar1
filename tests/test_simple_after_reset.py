#!/usr/bin/env python
"""
Тест после полного сброса миграций
"""
import os
import sys
import django
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')

print("🧪 ТЕСТ ПОСЛЕ ПОЛНОГО СБРОСА")
print("=" * 60)

try:
    django.setup()
    print("✅ Django настроен")
    
    from django.contrib.auth import get_user_model
    from catalog.models import Skin
    from inventory.models import UserSkin
    from django.db import connection
    
    User = get_user_model()
    
    # 1. Проверка таблицы в БД
    print("\n1. Проверка таблицы в БД...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_userskin';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("   ✅ Таблица 'inventory_userskin' существует")
            
            # Показываем структуру
            cursor.execute("PRAGMA table_info(inventory_userskin);")
            columns = cursor.fetchall()
            print("   Структура таблицы:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        else:
            print("   ❌ Таблица не существует!")
    
    # 2. Создание тестовых данных
    print("\n2. Создание тестовых данных...")
    
    # Пользователь
    user, u_created = User.objects.get_or_create(
        username='test_reset',
        defaults={'email': 'reset@test.com', 'is_active': True, 'kyc_verified': True}
    )
    if u_created:
        user.set_password('test123')
        user.save()
    
    # Скин
    skin, s_created = Skin.objects.get_or_create(
        name='[RESET] Test Skin',
        defaults={
            'skin_type': 'Weapon',
            'rarity': 'common',
            'price': Decimal('10.00'),
            'image_url': 'http://test.com/reset.jpg'
        }
    )
    
    print(f"   Пользователь: {user.username}")
    print(f"   Скин: {skin.name}")
    
    # 3. Тестирование создания UserSkin
    print("\n3. Тестирование UserSkin...")
    
    # Способ 1: Простое создание
    print("   a) Создание через objects.create()")
    try:
        user_skin1 = UserSkin.objects.create(
            user=user,
            skin=skin,
            quantity=5,
            status='available'
        )
        print(f"      ✅ Создан: {user_skin1}")
        print(f"        ID: {user_skin1.id}")
        print(f"        Quantity: {user_skin1.quantity}")
    except Exception as e:
        print(f"      ❌ Ошибка: {e}")
    
    # Способ 2: get_or_create
    print("\n   b) Создание через get_or_create()")
    try:
        user_skin2, created = UserSkin.objects.get_or_create(
            user=user,
            skin=skin,
            defaults={'quantity': 3}
        )
        print(f"      ✅ Получено/создано: {user_skin2}")
        print(f"        Created: {created}")
    except Exception as e:
        print(f"      ❌ Ошибка: {e}")
    
    # 4. Проверка данных
    print("\n4. Проверка данных в БД...")
    try:
        count = UserSkin.objects.count()
        print(f"   Всего записей UserSkin: {count}")
        
        user_skins = UserSkin.objects.filter(user=user)
        print(f"   Записей для пользователя {user.username}: {user_skins.count()}")
        
        for us in user_skins:
            print(f"     - {us.skin.name}: {us.quantity} шт., статус: {us.status}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 5. Очистка
    print("\n5. Очистка тестовых данных...")
    User.objects.filter(username='test_reset').delete()
    Skin.objects.filter(name='[RESET] Test Skin').delete()
    print("   ✅ Данные очищены")
    
    print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

input("\nНажмите Enter для выхода...")