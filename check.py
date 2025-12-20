#!/usr/bin/env python
import os
import sys
import django

# Установите правильный путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')

try:
    django.setup()
    print("✅ Django успешно настроен!")
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    print(f"✅ Модель User доступна")
    
    # Проверяем другие модели
    try:
        from inventory.models import UserSkin
        print(f"✅ Модель UserSkin доступна")
    except ImportError:
        print("❌ Модель UserSkin не найдена")
        
    # Пробуем создать тестовые данные
    user, created = User.objects.get_or_create(
        username='check_user',
        defaults={'email': 'check@test.com', 'is_active': True}
    )
    if created:
        user.set_password('test123')
        user.save()
        print("✅ Тестовый пользователь создан")
    
    print("\n🎉 Проект настроен корректно!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print(f"\n📁 Проверьте структуру проекта:")
    print(f"Текущая папка: {BASE_DIR}")
    print("\nДолжны быть файлы:")
    print("├── manage.py")
    print("├── skintrade/")
    print("│   └── settings.py")
    print("├── inventory/")
    print("│   └── models.py")
    print("└── ...")