from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Q
import logging

from .models import Order, Transaction as TradeTransaction
from inventory.models import UserSkin
from core.models import UserBalance

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Движок совпадения заявок с атомарными операциями"""
    
    @staticmethod
    def match_orders(skin_id):
        """
        Найти и исполнить совпадающие ордеры для конкретного скина
        Возвращает список исполненных сделок
        """
        logger.info(f"🔍 MatchingEngine: поиск совпадений для skin_id={skin_id}")
        
        # Атомарная операция для всего процесса
        try:
            with db_transaction.atomic():
                # Блокируем заявки для этого скина
                buy_orders = list(Order.objects.select_for_update().filter(
                    skin_id=skin_id,
                    order_type='BUY',
                    status='OPEN'
                ).order_by('-price', 'created_at'))
                
                sell_orders = list(Order.objects.select_for_update().filter(
                    skin_id=skin_id,
                    order_type='SELL',
                    status='OPEN'
                ).order_by('price', 'created_at'))
                
                if not buy_orders or not sell_orders:
                    logger.info(f"   ℹ️ Нет открытых заявок для совпадения")
                    return []
                
                executed_transactions = []
                
                # Алгоритм: цена покупки >= цены продажи
                buy_index = 0
                sell_index = 0
                
                while buy_index < len(buy_orders) and sell_index < len(sell_orders):
                    buy_order = buy_orders[buy_index]
                    sell_order = sell_orders[sell_index]
                    
                    logger.debug(f"   🔄 Проверка: BUY #{buy_order.id} @ {buy_order.price} "
                                 f"vs SELL #{sell_order.id} @ {sell_order.price}")
                    
                    # Проверяем совпадение цены
                    if buy_order.price >= sell_order.price:
                        # Вычисляем доступное количество
                        buy_available = buy_order.quantity - buy_order.filled_quantity
                        sell_available = sell_order.quantity - sell_order.filled_quantity
                        
                        # Проверяем наличие скинов у продавца
                        try:
                            seller_skin = UserSkin.objects.select_for_update().get(
                                user=sell_order.user,
                                skin__id=skin_id  # Исправлено: используем skin__id вместо skin_id
                            )
                            sell_available = min(sell_available, seller_skin.quantity)
                        except UserSkin.DoesNotExist:
                            sell_available = 0
                            logger.warning(f"   ⚠️ У продавца #{sell_order.user.id} нет скина #{skin_id}")
                        
                        # Проверяем баланс покупателя (с учетом комиссии 5%)
                        buyer_balance, _ = UserBalance.objects.select_for_update().get_or_create(
                            user=buy_order.user,
                            defaults={'amount': Decimal('0')}
                        )
                        
                        # Максимальное количество, которое может купить покупатель
                        max_price_per_item = sell_order.price * Decimal('1.05')  # цена + 5%
                        if max_price_per_item > 0:
                            buy_by_balance = int(buyer_balance.amount / max_price_per_item)
                        else:
                            buy_by_balance = 0
                        
                        # Итоговое количество для сделки
                        trade_quantity = min(buy_available, sell_available, buy_by_balance)
                        
                        logger.debug(f"   📊 Доступно: BUY={buy_available}, SELL={sell_available}, "
                                   f"BALANCE={buy_by_balance}, TRADE={trade_quantity}")
                        
                        if trade_quantity > 0:
                            # Выполняем сделку
                            try:
                                transaction = MatchingEngine._execute_trade(
                                    buy_order, sell_order, trade_quantity
                                )
                                executed_transactions.append(transaction)
                                logger.info(f"   ✅ Исполнена сделка #{transaction.id}")
                                
                                # Обновляем индексы если заявки исполнены полностью
                                if buy_order.filled_quantity >= buy_order.quantity:
                                    buy_index += 1
                                if sell_order.filled_quantity >= sell_order.quantity:
                                    sell_index += 1
                                    
                            except Exception as e:
                                logger.error(f"   ❌ Ошибка при исполнении сделки: {e}")
                                # Пропускаем эту пару заявок
                                buy_index += 1
                                sell_index += 1
                        else:
                            # Нет возможности для сделки - переходим к следующим заявкам
                            logger.debug(f"   ➡️ Нет возможности для сделки")
                            if buy_available == 0:
                                buy_index += 1
                            if sell_available == 0:
                                sell_index += 1
                            if buy_available > 0 and sell_available > 0:
                                # Есть заявки, но нет баланса/скинов
                                buy_index += 1
                    else:
                        # Цены не совпадают - переходим к следующей покупке
                        logger.debug(f"   ⬇️ Цены не совпадают: BUY {buy_order.price} < SELL {sell_order.price}")
                        buy_index += 1
                
                logger.info(f"   📊 Итог: исполнено {len(executed_transactions)} сделок")
                return executed_transactions
                
        except Exception as e:
            logger.error(f"❌ Ошибка MatchingEngine: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _execute_trade(buy_order, sell_order, quantity):
        """
        Исполнить сделку между двумя заявками
        Возвращает созданную транзакцию
        """
        with db_transaction.atomic():
            # 1. Рассчитываем суммы
            price_per_item = sell_order.price  # Исполняем по цене продавца
            total_amount = price_per_item * Decimal(quantity)
            fee = total_amount * Decimal('0.05')  # 5% комиссия
            total_with_fee = total_amount + fee
            
            logger.debug(f"   💰 Расчет: price={price_per_item}, qty={quantity}, "
                       f"total={total_amount}, fee={fee}, total_with_fee={total_with_fee}")
            
            # 2. Обновляем балансы
            buyer_balance = UserBalance.objects.select_for_update().get(user=buy_order.user)
            seller_balance, created = UserBalance.objects.select_for_update().get_or_create(
                user=sell_order.user,
                defaults={'amount': Decimal('0')}
            )
            
            # Проверяем баланс покупателя
            if not buyer_balance.has_sufficient_funds(total_with_fee):
                raise ValueError(
                    f"Недостаточно средств у покупателя #{buy_order.user.id}: "
                    f"{buyer_balance.amount} < {total_with_fee}"
                )
            
            # Списание с покупателя
            buyer_balance.withdraw(total_with_fee)
            
            # Зачисление продавцу (без комиссии)
            seller_balance.deposit(total_amount)
            
            # 3. Перемещаем скины
            # У продавца
            try:
                seller_skin = UserSkin.objects.select_for_update().get(
                    user=sell_order.user,
                    skin=buy_order.skin  # Исправлено: используем skin вместо skin_id
                )
                if seller_skin.quantity < quantity:
                    raise ValueError(
                        f"Недостаточно скинов у продавца #{sell_order.user.id}: "
                        f"{seller_skin.quantity} < {quantity}"
                    )
                
                seller_skin.quantity -= quantity
                if seller_skin.quantity <= 0:
                    seller_skin.delete()
                    logger.debug(f"   🗑️ Удален скин продавца #{sell_order.user.id}")
                else:
                    seller_skin.save()
                    logger.debug(f"   📉 У продавца осталось: {seller_skin.quantity}")
                    
            except UserSkin.DoesNotExist:
                raise ValueError(f"У продавца #{sell_order.user.id} нет скина #{buy_order.skin.id}")
            
            # У покупателя
            buyer_skin, created = UserSkin.objects.select_for_update().get_or_create(
                user=buy_order.user,
                skin=buy_order.skin,  # Исправлено: используем skin вместо skin_id
                defaults={'quantity': 0, 'status': 'available'}
            )
            if not created:
                buyer_skin.quantity += quantity
                buyer_skin.save()
                logger.debug(f"   📈 У покупателя стало: {buyer_skin.quantity}")
            else:
                logger.debug(f"   🆕 Создан скин покупателя")
            
            # 4. Обновляем заявки
            buy_order.filled_quantity += quantity
            sell_order.filled_quantity += quantity
            
            # Определяем новые статусы
            if buy_order.filled_quantity >= buy_order.quantity:
                buy_order.status = 'FILLED'
                logger.debug(f"   🟢 Заявка на покупку #{buy_order.id} полностью исполнена")
            elif buy_order.filled_quantity > 0:
                buy_order.status = 'PARTIAL'
                logger.debug(f"   🟡 Заявка на покупку #{buy_order.id} частично исполнена")
            
            if sell_order.filled_quantity >= sell_order.quantity:
                sell_order.status = 'FILLED'
                logger.debug(f"   🟢 Заявка на продажу #{sell_order.id} полностью исполнена")
            elif sell_order.filled_quantity > 0:
                sell_order.status = 'PARTIAL'
                logger.debug(f"   🟡 Заявка на продажу #{sell_order.id} частично исполнена")
            
            buy_order.save()
            sell_order.save()
            
            # 5. Создаем запись о сделке
            transaction = TradeTransaction.objects.create(
                buyer=buy_order.user,
                seller=sell_order.user,
                skin=buy_order.skin,
                price=price_per_item,
                quantity=quantity,
                order_buy=buy_order,
                order_sell=sell_order,
                fee=fee
            )
            
            logger.info(f"   💰 Создана транзакция #{transaction.id}")
            return transaction
    
    @staticmethod
    def process_all_pending_orders():
        """
        Обработать все ожидающие заявки для всех скинов
        Полезно для периодического запуска
        """
        from catalog.models import Skin
        
        all_transactions = []
        skins_with_orders = Skin.objects.filter(
            Q(order__status='OPEN') | Q(order__status='PARTIAL')
        ).distinct()
        
        logger.info(f"🔄 Обработка заявок для {skins_with_orders.count()} скинов")
        
        for skin in skins_with_orders:
            transactions = MatchingEngine.match_orders(skin.id)
            all_transactions.extend(transactions)
        
        logger.info(f"✅ Всего исполнено {len(all_transactions)} сделок")
        return all_transactions