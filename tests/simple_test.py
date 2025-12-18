#!/usr/bin/env python
"""
Простой диагностический тест для проверки моделей
"""
import os
import sys
import django
from decimal import Decimal

# Добавляем путь к проекту
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Ошибка настройки Django: {e}")
    print(f"   Проверьте, что файл settings.py существует в папке skintrade")
    print(f"   Текущий путь: {BASE_DIR}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from catalog.models import Skin
from core.models import UserBalance
from inventory.models import UserSkin
from trading.models import Order

User = get_user_model()

def test_basic_setup():
    """Базовый тест создания данных"""
    print("🧪 БАЗОВЫЙ ТЕСТ СОЗДАНИЯ ДАННЫХ")
    print("=" * 60)
    
    try:
        # 1. Проверяем модели
        print("1. Проверка моделей...")
        print(f"   User model: {User}")
        print(f"   UserSkin model: {UserSkin}")
        print(f"   Skin model: {Skin}")
        print(f"   UserBalance model: {UserBalance}")
        
        # Проверяем поля UserSkin
        print(f"\n   Поля UserSkin:")
        for field in UserSkin._meta.fields:
            print(f"      - {field.name}: {field.get_internal_type()}")
        
        # 2. Создаем простого пользователя
        print("\n2. Создание пользователя...")
        user, created = User.objects.get_or_create(
            username='test_diagnostic',
            defaults={'email': 'test@test.com', 'is_active': True}
        )
        if created:
            user.set_password('test123')
            user.save()
            print(f"   ✅ Пользователь создан: {user.username}")
        else:
            print(f"   ✅ Пользователь уже существует: {user.username}")
        
        # 3. Создаем скин
        print("\n3. Создание скина...")
        skin, created = Skin.objects.get_or_create(
            name='[DIAG] Test Skin',
            defaults={
                'skin_type': 'Weapon',
                'rarity': 'common',
                'price': Decimal('10.00'),
                'image_url': 'http://example.com/test.jpg'
            }
        )
        print(f"   ✅ Скин создан: {skin.name} (ID: {skin.id})")
        
        # 4. Пробуем создать UserSkin
        print("\n4. Создание UserSkin...")
        try:
            user_skin, created = UserSkin.objects.get_or_create(
                user=user,
                skin=skin,
                defaults={'quantity': 1, 'status': 'available'}
            )
            print(f"   ✅ UserSkin создан: {user_skin}")
            print(f"      ID: {user_skin.id}")
            print(f"      User: {user_skin.user.username}")
            print(f"      Skin: {user_skin.skin.name}")
            print(f"      Quantity: {user_skin.quantity}")
            
            # Проверяем, что можем получить скин по ID
            print(f"\n5. Проверка получения скина...")
            try:
                skin_by_id = Skin.objects.get(id=skin.id)
                print(f"   ✅ Скин получен по ID: {skin_by_id.name}")
            except Skin.DoesNotExist:
                print(f"   ❌ Не удалось получить скин по ID {skin.id}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания UserSkin: {e}")
            print(f"      Проверьте связь между UserSkin и Skin")
            return False
        
        # 5. Создаем баланс
        print("\n6. Создание баланса...")
        balance, created = UserBalance.objects.get_or_create(
            user=user,
            defaults={'amount': Decimal('100.00')}
        )
        print(f"   ✅ Баланс создан: {balance.amount} руб.")
        
        # 6. Создаем заявку
        print("\n7. Создание заявки...")
        order = Order.objects.create(
            user=user,
            skin=skin,
            order_type='BUY',
            price=Decimal('15.00'),
            quantity=1,
            status='OPEN'
        )
        print(f"   ✅ Заявка создана: #{order.id}")
        print(f"      User: {order.user.username}")
        print(f"      Skin: {order.skin.name}")
        print(f"      Price: {order.price}")
        
        print("\n✅ БАЗОВЫЙ ТЕСТ УСПЕШНО ЗАВЕРШЕН")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка в базовом тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_state():
    """Проверка состояния базы данных"""
    print("\n📊 СОСТОЯНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    try:
        print("Пользователи:")
        users = User.objects.all()[:5]
        for user in users:
            print(f"  - {user.username} (ID: {user.id}, KYC: {user.kyc_verified})")
        
        print("\nСкины:")
        skins = Skin.objects.all()[:5]
        for skin in skins:
            print(f"  - {skin.name} (ID: {skin.id}, Price: {skin.price})")
        
        print("\nUserSkins:")
        user_skins = UserSkin.objects.all()[:5]
        for user_skin in user_skins:
            print(f"  - {user_skin.user.username} -> {user_skin.skin.name} (x{user_skin.quantity})")
        
        print("\nБалансы:")
        balances = UserBalance.objects.all()[:5]
        for balance in balances:
            print(f"  - {balance.user.username}: {balance.amount} руб.")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")

def check_model_relationships():
    """Проверка связей между моделями"""
    print("\n🔗 ПРОВЕРКА СВЯЗЕЙ МЕЖДУ МОДЕЛЯМИ")
    print("=" * 60)
    
    try:
        # Проверяем User -> UserSkin
        user = User.objects.filter(username='test_diagnostic').first()
        if user:
            print(f"1. User -> UserSkin:")
            user_skins = user.user_skins.all()  # related_name из UserSkin
            print(f"   У пользователя {user.username} скинов: {user_skins.count()}")
        
        # Проверяем Skin -> UserSkin
        skin = Skin.objects.filter(name='[DIAG] Test Skin').first()
        if skin:
            print(f"\n2. Skin -> UserSkin:")
            skin_users = skin.user_skins.all()  # related_name из UserSkin
            print(f"   У скина {skin.name} владельцев: {skin_users.count()}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке связей: {e}")

if __name__ == '__main__':
    print("🔍 ДИАГНОСТИКА СИСТЕМЫ")
    print("=" * 60)
    
    # Запускаем базовый тест
    success = test_basic_setup()
    
    if success:
        # Проверяем состояние БД
        check_database_state()
        
        # Проверяем связи
        check_model_relationships()
        
        print("\n📝 РЕКОМЕНДАЦИИ:")
        print("1. Если тест прошел успешно, значит модели работают корректно")
        print("2. Запустите миграции если были изменения: python manage.py makemigrations && python manage.py migrate")
        print("3. Проверьте, что в inventory/models.py поле ForeignKey называется 'skin'")
        print("4. Убедитесь, что related_name в моделях не конфликтуют")
    else:
        print("\n❌ ДИАГНОСТИКА НЕ УДАЛАСЬ")
        print("\n🚨 ВОЗМОЖНЫЕ ПРОБЛЕМЫ:")
        print("1. Поле 'skin' не существует в модели UserSkin")
        print("2. Не применены миграции")
        print("3. Конфликт related_name в моделях")
        print("\n🛠️ РЕШЕНИЯ:")
        print("1. Проверьте inventory/models.py - поле должно быть 'skin = models.ForeignKey(Skin, ...)'")
        print("2. Запустите: python manage.py makemigrations inventory")
        print("3. Запустите: python manage.py migrate inventory")