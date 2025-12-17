import requests
import json

print("=" * 60)
print("ТЕСТИРОВАНИЕ API БЕЗ АВТОРИЗАЦИИ")
print("=" * 60)

BASE_URL = "http://127.0.0.1:8000/api/trading"

# 1. Проверяем GET запросы
print("\n1. GET /orders/ - список заявок")
try:
    response = requests.get(f"{BASE_URL}/orders/")
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
except Exception as e:
    print(f"   Ошибка: {e}")

# 2. Создаём заявку на ПОКУПКУ
print("\n2. POST /order/create/ - создаём заявку BUY")
buy_data = {
    "skin": 1,           # ID созданного скина
    "order_type": "BUY",
    "price": "160.00",   # Цена как строка!
    "quantity": 2
}

try:
    response = requests.post(
        f"{BASE_URL}/order/create/",
        json=buy_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print("   ✅ УСПЕХ! Заявка создана")
        print(f"   ID заявки: {result['order']['id']}")
        print(f"   Тип: {result['order']['order_type']}")
        print(f"   Цена: {result['order']['price']}")
        print(f"   Статус: {result['order']['status']}")
        print(f"   Исполнено сделок: {result['executed_transactions']}")
        
        # Сохраняем ID заявки для возможной отмены
        buy_order_id = result['order']['id']
    else:
        print(f"   ❌ Ошибка: {response.text}")
        
except Exception as e:
    print(f"   ❌ Ошибка соединения: {e}")

# 3. Создаём заявку на ПРОДАЖУ (для теста матчинга)
print("\n3. POST /order/create/ - создаём заявку SELL")
sell_data = {
    "skin": 1,
    "order_type": "SELL",
    "price": "150.00",   # Ниже BUY цены - должно сматчиться!
    "quantity": 1
}

try:
    response = requests.post(
        f"{BASE_URL}/order/create/",
        json=sell_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"   Исполнено сделок: {result.get('executed_transactions', 0)}")
        
        if result.get('executed_transactions', 0) > 0:
            print("   🎉 СДЕЛКА ИСПОЛНЕНА! Матчинг работает!")
        else:
            print("   ⚠️ Сделка не исполнилась (нет совпадения по цене)")
    else:
        print(f"   ❌ Ошибка: {response.text}")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 4. Проверяем итоговое состояние
print("\n4. Проверяем итоговое состояние...")

# 4.1 Заявки
print("   GET /orders/ - все заявки")
try:
    response = requests.get(f"{BASE_URL}/orders/")
    orders = response.json()
    print(f"   Всего заявок: {len(orders)}")
    
    for order in orders:
        status_icon = "✅" if order['status'] == 'FILLED' else "⏳"
        print(f"   {status_icon} Заявка #{order['id']}: {order['order_type']} "
              f"по {order['price']} (статус: {order['status']})")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 4.2 Транзакции
print("\n   GET /transactions/ - все сделки")
try:
    response = requests.get(f"{BASE_URL}/transactions/")
    transactions = response.json()
    print(f"   Всего сделок: {len(transactions)}")
    
    for tx in transactions:
        print(f"   💰 Сделка #{tx['id']}: {tx['quantity']}шт по {tx['price']}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "=" * 60)
print("ТЕСТ ЗАВЕРШЁН")
print("=" * 60)