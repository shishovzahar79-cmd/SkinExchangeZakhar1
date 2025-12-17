from decimal import Decimal
from django.db import transaction as db_transaction
from .models import Order, Transaction
from inventory.models import UserSkin

class MatchingEngine:
    """Движок совпадения заявок"""
    
    @staticmethod
    def match_orders(skin_id):
        """Найти и исполнить совпадающие ордеры для конкретного скина"""
        # Берем заявки на покупку (от высокой цены к низкой)
        buy_orders = Order.objects.filter(
            skin_id=skin_id,
            order_type='BUY',
            status='OPEN'
        ).order_by('-price', 'created_at')
        
        # Берем заявки на продажу (от низкой цены к высокой)
        sell_orders = Order.objects.filter(
            skin_id=skin_id,
            order_type='SELL',
            status='OPEN'
        ).order_by('price', 'created_at')
        
        executed_transactions = []
        
        for buy_order in buy_orders:
            if buy_order.status != 'OPEN':
                continue
                
            for sell_order in sell_orders:
                if sell_order.status != 'OPEN':
                    continue
                    
                # Проверяем совпадение цены
                if buy_order.price >= sell_order.price:
                    # Вычисляем доступное количество для сделки
                    buy_available = buy_order.quantity - buy_order.filled_quantity
                    sell_available = sell_order.quantity - sell_order.filled_quantity
                    trade_quantity = min(buy_available, sell_available)
                    
                    if trade_quantity > 0:
                        with db_transaction.atomic():
                            # Создаем транзакцию
                            transaction = Transaction.objects.create(
                                buyer=buy_order.user,
                                seller=sell_order.user,
                                skin=buy_order.skin,
                                price=sell_order.price,  # Цена продавца
                                quantity=trade_quantity,
                                order_buy=buy_order,
                                order_sell=sell_order,
                                fee=sell_order.price * Decimal(trade_quantity) * Decimal('0.05')  # 5% комиссия
                            )
                            
                            # Обновляем статусы ордеров
                            buy_order.filled_quantity += trade_quantity
                            sell_order.filled_quantity += trade_quantity
                            
                            if buy_order.filled_quantity >= buy_order.quantity:
                                buy_order.status = 'FILLED'
                            else:
                                buy_order.status = 'PARTIAL'
                                
                            if sell_order.filled_quantity >= sell_order.quantity:
                                sell_order.status = 'FILLED'
                            else:
                                sell_order.status = 'PARTIAL'
                            
                            buy_order.save()
                            sell_order.save()
                            
                            # Перемещаем скины
                            MatchingEngine._transfer_skin(
                                skin=buy_order.skin,
                                from_user=sell_order.user,
                                to_user=buy_order.user,
                                quantity=trade_quantity
                            )
                            
                            executed_transactions.append(transaction)
        
        return executed_transactions
    
    @staticmethod
    def _transfer_skin(skin, from_user, to_user, quantity):
        """Переместить скин между пользователями"""
        # Убираем у продавца
        try:
            user_skin_seller = UserSkin.objects.get(
                user=from_user,
                skin=skin
            )
            user_skin_seller.quantity -= quantity
            if user_skin_seller.quantity <= 0:
                user_skin_seller.delete()
            else:
                user_skin_seller.save()
        except UserSkin.DoesNotExist:
            pass  # У продавца уже нет этого скина
        
        # Добавляем покупателю
        user_skin_buyer, created = UserSkin.objects.get_or_create(
            user=to_user,
            skin=skin,
            defaults={'quantity': quantity}
        )
        if not created:
            user_skin_buyer.quantity += quantity
            user_skin_buyer.save()