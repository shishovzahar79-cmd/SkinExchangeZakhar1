#!/usr/bin/env python
"""
Тестовый скрипт для проверки торговой системы
"""
import os
import sys
import django
from decimal import Decimal
from django.db.models import Q

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skintrade.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from catalog.models import Skin
from core.models import UserBalance
from inventory.models import UserSkin
from trading.models import Order, Transaction
from trading.matching_engine import MatchingEngine

User = get_user_model()

class TradingTester:
    """Тестирование торговой системы"""
    
    def __init__(self):
        self.users = {}
        self.skins = {}
        self.orders = []
    
    def cleanup_test_data(self):
        """Очистка тестовых данных"""
        print("🧹 Очистка старых тестовых данных...")
        
        # Удаляем тестовых пользователей (кроме admin)
        User.objects.filter(
            username__in=['test_buyer', 'test_seller', 'test_buyer2', 'test_seller2', 'test_nokyc']
        ).delete()
        
        # Удаляем тестовые скины
        Skin.objects.filter(name__contains='[TEST]').delete()
        
        # Удаляем тестовые заявки и транзакции
        Order.objects.filter(user__username__startswith='test_').delete()
        
        # Используем Q объекты для OR условий
        Transaction.objects.filter(
            Q(buyer__username__startswith='test_') | 
            Q(seller__username__startswith='test_')
        ).delete()
        
        print("✅ Старые данные очищены")
    
    def setup_test_data(self):
        """Создание тестовых данных"""
        print("=" * 60)
        print("🧪 НАСТРОЙКА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 60)
        
        # Очистка старых данных
        self.cleanup_test_data()
        
        try:
            # Создаем покупателя
            buyer, buyer_created = User.objects.get_or_create(
                username='test_buyer',
                defaults={
                    'email': 'buyer@test.com',
                    'kyc_verified': True,
                    'is_active': True
                }
            )
            if buyer_created:
                buyer.set_password('test123')
                buyer.save()
            
            # Создаем продавца
            seller, seller_created = User.objects.get_or_create(
                username='test_seller',
                defaults={
                    'email': 'seller@test.com',
                    'kyc_verified': True,
                    'is_active': True
                }
            )
            if seller_created:
                seller.set_password('test123')
                seller.save()
            
            # Сохраняем в словарь
            self.users['buyer'] = buyer
            self.users['seller'] = seller
            
            # Создаем или получаем балансы
            buyer_balance, _ = UserBalance.objects.get_or_create(
                user=buyer,
                defaults={'amount': Decimal('1000.00')}
            )
            buyer_balance.amount = Decimal('1000.00')
            buyer_balance.save()
            
            seller_balance, _ = UserBalance.objects.get_or_create(
                user=seller,
                defaults={'amount': Decimal('500.00')}
            )
            seller_balance.amount = Decimal('500.00')
            seller_balance.save()
            
            # Создаем тестовый скин
            skin, skin_created = Skin.objects.get_or_create(
                name='[TEST] AK-47 | Redline',
                defaults={
                    'skin_type': 'Rifle',
                    'rarity': 'rare',
                    'price': Decimal('50.00'),
                    'image_url': 'http://example.com/redline.jpg',
                    'metadata': {'game': 'CS2', 'wear': 'Field-Tested'}
                }
            )
            self.skins['ak47'] = skin
            
            # Добавляем скин продавцу - ИСПРАВЛЕННЫЙ КОД
            user_skin, created = UserSkin.objects.get_or_create(
                user=seller,
                skin=skin,  # Используем объект skin
                defaults={'quantity': 3, 'status': 'available'}
            )
            if not created:
                user_skin.quantity = 3
                user_skin.status = 'available'
                user_skin.save()
            
            # Вывод информации
            print(f"✅ Пользователи созданы:")
            print(f"   👤 Покупатель: {self.users['buyer'].username}")
            print(f"      Баланс: {self.users['buyer'].balance}")
            print(f"      KYC: {'✅' if self.users['buyer'].kyc_verified else '❌'}")
            
            print(f"\n   👤 Продавец: {self.users['seller'].username}")
            print(f"      Баланс: {self.users['seller'].balance}")
            print(f"      KYC: {'✅' if self.users['seller'].kyc_verified else '❌'}")
            
            seller_skin = UserSkin.objects.get(user=self.users['seller'], skin=self.skins['ak47'])
            print(f"      Скины AK-47: {seller_skin.quantity} шт.")
            
            print(f"\n   🎮 Скин: {self.skins['ak47'].name}")
            print(f"      Цена: {self.skins['ak47'].price} руб.")
            print(f"      Тип: {self.skins['ak47'].skin_type}")
            print(f"      Редкость: {self.skins['ak47'].get_rarity_display()}")
            
            print(f"\n   💰 Балансы:")
            print(f"      Покупатель: {buyer_balance.amount} руб.")
            print(f"      Продавец: {seller_balance.amount} руб.")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при создании тестовых данных: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_simple_trade(self):
        """Тест простой сделки"""
        print("\n" + "=" * 60)
        print("🧪 ТЕСТ 1: ПРОСТАЯ СДЕЛКА")
        print("=" * 60)
        
        try:
            # Создаем заявку на продажу (45 рублей)
            sell_order = Order.objects.create(
                user=self.users['seller'],
                skin=self.skins['ak47'],
                order_type='SELL',
                price=Decimal('45.00'),
                quantity=2,
                status='OPEN'
            )
            print(f"📤 Создана заявка на ПРОДАЖУ:")
            print(f"   ID: #{sell_order.id}")
            print(f"   Цена: {sell_order.price} руб.")
            print(f"   Количество: {sell_order.quantity} шт.")
            print(f"   Пользователь: {sell_order.user.username}")
            
            # Создаем заявку на покупку (50 рублей)
            buy_order = Order.objects.create(
                user=self.users['buyer'],
                skin=self.skins['ak47'],
                order_type='BUY',
                price=Decimal('50.00'),
                quantity=1,
                status='OPEN'
            )
            print(f"\n📥 Создана заявка на ПОКУПКУ:")
            print(f"   ID: #{buy_order.id}")
            print(f"   Цена: {buy_order.price} руб.")
            print(f"   Количество: {buy_order.quantity} шт.")
            print(f"   Пользователь: {buy_order.user.username}")
            
            # Запускаем движок совпадения
            print(f"\n🔍 Запуск MatchingEngine...")
            transactions = MatchingEngine.match_orders(self.skins['ak47'].id)
            
            # Обновляем данные
            sell_order.refresh_from_db()
            buy_order.refresh_from_db()
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"   Исполнено сделок: {len(transactions)}")
            
            if transactions:
                transaction = transactions[0]
                print(f"\n   💰 СДЕЛКА #{transaction.id}:")
                print(f"      Цена: {transaction.price} руб.")
                print(f"      Количество: {transaction.quantity} шт.")
                print(f"      Комиссия: {transaction.fee:.2f} руб.")
                print(f"      Покупатель: {transaction.buyer.username}")
                print(f"      Продавец: {transaction.seller.username}")
                print(f"      Дата: {transaction.created_at}")
            
            print(f"\n   📈 СТАТУСЫ ЗАЯВОК:")
            print(f"      Заявка на продажу #{sell_order.id}: {sell_order.get_status_display()}")
            print(f"      Исполнено: {sell_order.filled_quantity}/{sell_order.quantity}")
            
            print(f"      Заявка на покупку #{buy_order.id}: {buy_order.get_status_display()}")
            print(f"      Исполнено: {buy_order.filled_quantity}/{buy_order.quantity}")
            
            # Проверяем балансы
            buyer_balance = UserBalance.objects.get(user=self.users['buyer'])
            seller_balance = UserBalance.objects.get(user=self.users['seller'])
            
            print(f"\n   💳 БАЛАНСЫ ПОСЛЕ СДЕЛКИ:")
            print(f"      Покупатель: {buyer_balance.amount:.2f} руб.")
            print(f"      Продавец: {seller_balance.amount:.2f} руб.")
            
            # Проверяем инвентарь
            try:
                buyer_skin = UserSkin.objects.get(user=self.users['buyer'], skin=self.skins['ak47'])
                print(f"      У покупателя скинов: {buyer_skin.quantity} шт.")
            except UserSkin.DoesNotExist:
                print(f"      У покупателя нет скина")
            
            try:
                seller_skin = UserSkin.objects.get(user=self.users['seller'], skin=self.skins['ak47'])
                print(f"      У продавца скинов: {seller_skin.quantity} шт.")
            except UserSkin.DoesNotExist:
                print(f"      У продавца нет скина")
            
            # Проверяем успешность теста
            success = len(transactions) > 0
            if success:
                print(f"\n✅ ТЕСТ ПРОЙДЕН: Сделка успешно исполнена")
            else:
                print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: Сделка не исполнена")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_partial_fill(self):
        """Тест частичного исполнения"""
        print("\n" + "=" * 60)
        print("🧪 ТЕСТ 2: ЧАСТИЧНОЕ ИСПОЛНЕНИЕ")
        print("=" * 60)
        
        try:
            # Сбрасываем тестовые данные
            self.setup_test_data()
            
            # Продавец хочет продать 3 скина
            sell_order = Order.objects.create(
                user=self.users['seller'],
                skin=self.skins['ak47'],
                order_type='SELL',
                price=Decimal('48.00'),
                quantity=3,
                status='OPEN'
            )
            
            # Покупатель хочет купить 2 скина
            buy_order = Order.objects.create(
                user=self.users['buyer'],
                skin=self.skins['ak47'],
                order_type='BUY',
                price=Decimal('50.00'),
                quantity=2,
                status='OPEN'
            )
            
            print(f"📤 Заявка на продажу: 3 шт. по {sell_order.price} руб.")
            print(f"📥 Заявка на покупку: 2 шт. по {buy_order.price} руб.")
            
            # Запускаем движок
            transactions = MatchingEngine.match_orders(self.skins['ak47'].id)
            
            # Обновляем данные
            sell_order.refresh_from_db()
            buy_order.refresh_from_db()
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"   Исполнено сделок: {len(transactions)}")
            print(f"   Статус продажи: {sell_order.get_status_display()} (исполнено: {sell_order.filled_quantity}/3)")
            print(f"   Статус покупки: {buy_order.get_status_display()} (исполнено: {buy_order.filled_quantity}/2)")
            
            # Проверяем успешность теста
            success = sell_order.status == 'PARTIAL' and buy_order.status == 'FILLED'
            if success:
                print(f"   ✅ Частичное исполнение работает корректно!")
                print(f"   ✅ ТЕСТ ПРОЙДЕН")
            else:
                print(f"   ❌ Ожидалось: продажа=PARTIAL, покупка=FILLED")
                print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_price_priority(self):
        """Тест приоритета цен"""
        print("\n" + "=" * 60)
        print("🧪 ТЕСТ 3: ПРИОРИТЕТ ЦЕН (FIFO)")
        print("=" * 60)
        
        try:
            self.setup_test_data()
            
            print("Создаем несколько заявок на покупку:")
            
            # Создаем несколько заявок на покупку с разными ценами
            buy_orders = []
            prices = [Decimal('52.00'), Decimal('51.00'), Decimal('50.00')]
            
            for i, price in enumerate(prices, 1):
                order = Order.objects.create(
                    user=self.users['buyer'],
                    skin=self.skins['ak47'],
                    order_type='BUY',
                    price=price,
                    quantity=1,
                    status='OPEN'
                )
                buy_orders.append(order)
                print(f"   {i}. Покупка: {price} руб. (ID: #{order.id})")
            
            # Заявка на продажу
            sell_order = Order.objects.create(
                user=self.users['seller'],
                skin=self.skins['ak47'],
                order_type='SELL',
                price=Decimal('49.00'),
                quantity=1,
                status='OPEN'
            )
            print(f"\n   Заявка на продажу: {sell_order.price} руб. (ID: #{sell_order.id})")
            
            # Запускаем движок
            transactions = MatchingEngine.match_orders(self.skins['ak47'].id)
            
            if transactions:
                transaction = transactions[0]
                print(f"\n📊 РЕЗУЛЬТАТЫ:")
                print(f"   Исполнена сделка по цене: {transaction.price} руб.")
                print(f"   Цена продавца: {sell_order.price} руб.")
                print(f"   Исполнена с заявкой покупки: #{transaction.order_buy.id} по {transaction.order_buy.price} руб.")
                
                # Проверяем, что исполнилась заявка с самой высокой ценой
                highest_buy = max(buy_orders, key=lambda o: o.price)
                if transaction.order_buy == highest_buy:
                    print(f"   ✅ Приоритет цен работает: исполнилась заявка с самой высокой ценой ({highest_buy.price} руб.)")
                    print(f"   ✅ ТЕСТ ПРОЙДЕН")
                    return True
                else:
                    print(f"   ❌ Ошибка приоритета: должна была исполниться заявка по {highest_buy.price} руб.")
                    print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН")
                    return False
            else:
                print(f"\n❌ Сделка не исполнена")
                print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН")
                return False
                
        except Exception as e:
            print(f"\n❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_insufficient_funds(self):
        """Тест недостаточности средств"""
        print("\n" + "=" * 60)
        print("🧪 ТЕСТ 4: НЕДОСТАТОЧНОСТЬ СРЕДСТВ")
        print("=" * 60)
        
        try:
            self.setup_test_data()
            
            # Уменьшаем баланс покупателя
            buyer_balance = UserBalance.objects.get(user=self.users['buyer'])
            buyer_balance.amount = Decimal('10.00')  # Очень мало денег
            buyer_balance.save()
            
            print(f"💰 Баланс покупателя уменьшен до: {buyer_balance.amount} руб.")
            
            # Заявка на продажу
            sell_order = Order.objects.create(
                user=self.users['seller'],
                skin=self.skins['ak47'],
                order_type='SELL',
                price=Decimal('20.00'),
                quantity=1,
                status='OPEN'
            )
            
            # Заявка на покупку (покупатель не может купить из-за комиссии)
            buy_order = Order.objects.create(
                user=self.users['buyer'],
                skin=self.skins['ak47'],
                order_type='BUY',
                price=Decimal('20.00'),
                quantity=1,
                status='OPEN'
            )
            
            print(f"\n📤 Заявка на продажу: {sell_order.price} руб.")
            print(f"📥 Заявка на покупку: {buy_order.price} руб.")
            print(f"   (покупателю нужно {buy_order.price * Decimal('1.05'):.2f} руб. с учетом комиссии)")
            
            # Запускаем движок
            transactions = MatchingEngine.match_orders(self.skins['ak47'].id)
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"   Исполнено сделок: {len(transactions)}")
            
            if len(transactions) == 0:
                print(f"   ✅ Движок корректно не исполнил сделку при недостаточном балансе")
                print(f"   ✅ ТЕСТ ПРОЙДЕН")
                return True
            else:
                print(f"   ❌ Движок должен был не исполнить сделку")
                print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН")
                return False
                
        except Exception as e:
            print(f"\n❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_no_kyc(self):
        """Тест отсутствия KYC"""
        print("\n" + "=" * 60)
        print("🧪 ТЕСТ 5: ОТСУТСТВИЕ KYC")
        print("=" * 60)
        
        try:
            # Создаем пользователя без KYC
            no_kyc_user, created = User.objects.get_or_create(
                username='test_nokyc',
                defaults={
                    'email': 'nokyc@test.com',
                    'kyc_verified': False,
                    'is_active': True
                }
            )
            if created:
                no_kyc_user.set_password('test123')
                no_kyc_user.save()
            
            # Добавляем баланс
            balance, _ = UserBalance.objects.get_or_create(
                user=no_kyc_user,
                defaults={'amount': Decimal('1000.00')}
            )
            
            print(f"👤 Пользователь без KYC: {no_kyc_user.username}")
            print(f"   KYC статус: {'✅' if no_kyc_user.kyc_verified else '❌'} ({no_kyc_user.kyc_status})")
            print(f"   Баланс: {balance.amount} руб.")
            
            # Пытаемся создать заявку
            try:
                order = Order.objects.create(
                    user=no_kyc_user,
                    skin=self.skins['ak47'],
                                        order_type='BUY',
                    price=Decimal('50.00'),
                    quantity=1,
                    status='OPEN'
                )
                print(f"\n❌ Заявка создана без KYC - ЭТО ОШИБКА!")
                print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН")
                
                # Удаляем тестового пользователя
                no_kyc_user.delete()
                return False
                
            except Exception as e:
                # В идеале здесь должна быть проверка в CreateOrderView
                print(f"\n⚠️ Заявка не создана (ожидаемое поведение)")
                print(f"   Примечание: проверка KYC должна быть в API, а не в модели")
                print(f"   ✅ ТЕСТ УСЛОВНО ПРОЙДЕН")
                
                # Удаляем тестового пользователя
                no_kyc_user.delete()
                return True
                
        except Exception as e:
            print(f"\n❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ ТОРГОВОЙ СИСТЕМЫ")
        print("=" * 60)
        
        test_results = []
        
        try:
            # Тест 1: Простая сделка
            print("\n" + "=" * 60)
            print("🧪 ТЕСТ 1: ПРОСТАЯ СДЕЛКА")
            print("=" * 60)
            
            if self.setup_test_data():
                result1 = self.test_simple_trade()
                test_results.append(("1. Простая сделка", result1))
            else:
                test_results.append(("1. Простая сделка", False))
            
            # Тест 2: Частичное исполнение
            print("\n" + "=" * 60)
            print("🧪 ТЕСТ 2: ЧАСТИЧНОЕ ИСПОЛНЕНИЕ")
            print("=" * 60)
            
            result2 = self.test_partial_fill()
            test_results.append(("2. Частичное исполнение", result2))
            
            # Тест 3: Приоритет цен
            print("\n" + "=" * 60)
            print("🧪 ТЕСТ 3: ПРИОРИТЕТ ЦЕН (FIFO)")
            print("=" * 60)
            
            result3 = self.test_price_priority()
            test_results.append(("3. Приоритет цен", result3))
            
            # Тест 4: Недостаточность средств
            print("\n" + "=" * 60)
            print("🧪 ТЕСТ 4: НЕДОСТАТОЧНОСТЬ СРЕДСТВ")
            print("=" * 60)
            
            result4 = self.test_insufficient_funds()
            test_results.append(("4. Недостаточность средств", result4))
            
            # Тест 5: Отсутствие KYC
            print("\n" + "=" * 60)
            print("🧪 ТЕСТ 5: ОТСУТСТВИЕ KYC")
            print("=" * 60)
            
            result5 = self.test_no_kyc()
            test_results.append(("5. Отсутствие KYC", result5))
            
            # Итоговый отчет
            print("\n" + "=" * 60)
            print("📋 ИТОГОВЫЙ ОТЧЕТ")
            print("=" * 60)
            
            for test_name, result in test_results:
                status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
                print(f"{test_name}: {status}")
            
            passed = sum(1 for _, result in test_results if result)
            total = len(test_results)
            
            print(f"\n📊 ИТОГО: {passed}/{total} тестов пройдено")
            
            if passed == total:
                print("\n🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
            else:
                print(f"\n⚠️ {total - passed} тестов не пройдено")
            
            return passed == total
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_admin_user():
    """Создание администратора для тестов"""
    print("\n👑 СОЗДАНИЕ АДМИНИСТРАТОРА")
    print("=" * 60)
    
    try:
        # Проверяем, существует ли уже админ
        admin_exists = User.objects.filter(username='admin').exists()
        
        if not admin_exists:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@skintrade.com',
                password='admin123'
            )
            
            # Добавляем баланс
            UserBalance.objects.create(user=admin, amount=Decimal('10000.00'))
            
            print(f"✅ Администратор создан:")
            print(f"   Логин: admin")
            print(f"   Пароль: admin123")
            print(f"   Баланс: 10000.00 руб.")
            print(f"   KYC: ✅ верифицирован")
            
            return admin
        else:
            print(f"✅ Администратор уже существует")
            admin = User.objects.get(username='admin')
            
            # Обновляем пароль на случай если тестируем
            admin.set_password('admin123')
            admin.save()
            
            # Создаем баланс если нет
            UserBalance.objects.get_or_create(
                user=admin,
                defaults={'amount': Decimal('10000.00')}
            )
            
            print(f"   Логин: admin")
            print(f"   Пароль: admin123")
            print(f"   Баланс: {admin.balance} руб.")
            
            return admin
            
    except Exception as e:
        print(f"⚠️ Ошибка при работе с администратором: {e}")
        return None

def quick_api_test():
    """Быстрый тест создания заявки вручную"""
    print("\n⚡ БЫСТРЫЙ РУЧНОЙ ТЕСТ")
    print("=" * 60)
    
    try:
        # Создаем тестовые данные
        tester = TradingTester()
        if not tester.setup_test_data():
            print("❌ Не удалось создать тестовые данные для API теста")
            return
        
        print("\n📝 Ручное тестирование заявок:")
        
        # Тест 1: Создание заявки на покупку
        print("\n1. Создание заявки на покупку...")
        buy_order = Order.objects.create(
            user=tester.users['buyer'],
            skin=tester.skins['ak47'],
            order_type='BUY',
            price=Decimal('55.00'),
            quantity=1,
            status='OPEN'
        )
        print(f"   ✅ Заявка создана: #{buy_order.id}")
        
        # Тест 2: Создание заявки на продажу
        print("\n2. Создание заявки на продажу...")
        sell_order = Order.objects.create(
            user=tester.users['seller'],
            skin=tester.skins['ak47'],
            order_type='SELL',
            price=Decimal('50.00'),
            quantity=1,
            status='OPEN'
        )
        print(f"   ✅ Заявка создана: #{sell_order.id}")
        
        # Тест 3: Запуск движка
        print("\n3. Запуск MatchingEngine...")
        transactions = MatchingEngine.match_orders(tester.skins['ak47'].id)
        print(f"   ✅ Исполнено сделок: {len(transactions)}")
        
        if transactions:
            transaction = transactions[0]
            print(f"\n   💰 Детали сделки:")
            print(f"      ID: #{transaction.id}")
            print(f"      Цена: {transaction.price} руб.")
            print(f"      Количество: {transaction.quantity}")
            print(f"      Комиссия: {transaction.fee:.2f} руб.")
            print(f"      Покупатель: {transaction.buyer.username}")
            print(f"      Продавец: {transaction.seller.username}")
        
        # Проверяем балансы
        buyer_balance = UserBalance.objects.get(user=tester.users['buyer'])
        seller_balance = UserBalance.objects.get(user=tester.users['seller'])
        
        print(f"\n   💳 Итоговые балансы:")
        print(f"      Покупатель: {buyer_balance.amount:.2f} руб.")
        print(f"      Продавец: {seller_balance.amount:.2f} руб.")
        
        print("\n✅ Ручное тестирование завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при ручном тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🚀 ЗАПУСК ТЕСТОВОЙ СИСТЕМЫ ТОРГОВЛИ")
    print("=" * 60)
    
    # Создаем администратора
    admin = create_admin_user()
    
    # Запускаем тесты
    tester = TradingTester()
    success = tester.run_all_tests()
    
    # Быстрый ручной тест
    quick_api_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    else:
        print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
    
    print("\n📝 КРАТКАЯ ИНСТРУКЦИЯ:")
    print("1. Запустите сервер: python manage.py runserver")
    print("2. Админка: http://localhost:8000/admin/ (логин: admin, пароль: admin123)")
    print("3. API доступен по: http://localhost:8000/api/trading/")
    print("4. Тестовые пользователи:")
    print("   - test_buyer / test123")
    print("   - test_seller / test123")
    print("   - test_nokyc / test123 (без KYC)")
    
    # Очищаем тестовые данные в конце
    tester.cleanup_test_data()