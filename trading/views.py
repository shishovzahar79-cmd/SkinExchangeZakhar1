from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from django.db import transaction as db_transaction
from django.db.models import Q
from decimal import Decimal
import logging

from .models import Order, Transaction
from .serializers import OrderSerializer, TransactionSerializer
from .matching_engine import MatchingEngine
from inventory.models import UserSkin
from core.models import UserBalance

logger = logging.getLogger(__name__)

class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class CreateOrderView(APIView):
    """Создание торговой заявки"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Создать заявку на покупку/продажу
        Пример тела запроса:
        {
            "skin": 1,
            "order_type": "BUY",
            "price": "100.00",
            "quantity": 2
        }
        """
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            data = serializer.validated_data
            order_type = data.get('order_type')
            skin = data.get('skin')
            price = data.get('price')
            quantity = data.get('quantity', 1)
            
            logger.info(f"📝 Создание заявки: user={user.id}, type={order_type}, "
                       f"skin={skin.id}, price={price}, qty={quantity}")
            
            # 1. Проверка KYC
            if not user.kyc_verified:
                logger.warning(f"   ❌ KYC не пройден для user={user.id}")
                return Response(
                    {
                        'error': 'Для торговли требуется KYC-верификация',
                        'code': 'KYC_REQUIRED'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                with db_transaction.atomic():
                    # 2. Проверки для заявки на продажу
                    if order_type == 'SELL':
                        # Проверяем наличие скинов
                        try:
                            user_skin = UserSkin.objects.select_for_update().get(
                                user=user,
                                skin=skin
                            )
                            available_qty = user_skin.get_available_quantity()
                            
                            if available_qty < quantity:
                                logger.warning(f"   ❌ Недостаточно скинов: user={user.id}, "
                                             f"skin={skin.id}, available={available_qty}, requested={quantity}")
                                return Response(
                                    {
                                        'error': f'Недостаточно скинов',
                                        'available': available_qty,
                                        'requested': quantity,
                                        'code': 'INSUFFICIENT_SKINS'
                                    },
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                            
                            # В реальной системе здесь нужно зарезервировать скины
                            # user_skin.reserve(quantity)
                            
                        except UserSkin.DoesNotExist:
                            logger.warning(f"   ❌ Скин не найден в инвентаре: user={user.id}, skin={skin.id}")
                            return Response(
                                {
                                    'error': 'Скин не найден в вашем инвентаре',
                                    'code': 'SKIN_NOT_FOUND'
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    # 3. Проверки для заявки на покупку
                    elif order_type == 'BUY':
                        if price <= Decimal('0'):
                            return Response(
                                {
                                    'error': 'Цена должна быть положительной',
                                    'code': 'INVALID_PRICE'
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Проверяем баланс
                        balance, created = UserBalance.objects.select_for_update().get_or_create(
                            user=user,
                            defaults={'amount': Decimal('0')}
                        )
                        
                        # Резервируем максимальную сумму (цена × количество + 5% комиссия)
                        max_amount = price * Decimal(quantity) * Decimal('1.05')
                        
                        if not balance.has_sufficient_funds(max_amount):
                            logger.warning(f"   ❌ Недостаточно средств: user={user.id}, "
                                         f"balance={balance.amount}, required={max_amount}")
                            return Response(
                                {
                                    'error': f'Недостаточно средств',
                                    'available': float(balance.amount),
                                    'required': float(max_amount),
                                    'code': 'INSUFFICIENT_FUNDS'
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # В реальной системе здесь нужно зарезервировать средства
                        # balance.reserve(max_amount)
                    
                    else:
                        return Response(
                            {'error': 'Неверный тип заявки', 'code': 'INVALID_ORDER_TYPE'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # 4. Создаем заявку
                    order = serializer.save(
                        user=user,
                        status='OPEN',
                        filled_quantity=0
                    )
                    
                    logger.info(f"   ✅ Заявка создана: #{order.id}")
                    
                    # 5. Запускаем движок совпадения
                    try:
                        transactions = MatchingEngine.match_orders(skin.id)
                        executed_count = len(transactions)
                        logger.info(f"   🔄 Исполнено сделок: {executed_count}")
                    except Exception as e:
                        logger.error(f"   ⚠️ Ошибка MatchingEngine: {e}", exc_info=True)
                        transactions = []
                        executed_count = 0
                    
                    # 6. Обновляем данные заявки
                    order.refresh_from_db()
                    
                    response_data = {
                        'order': OrderSerializer(order).data,
                        'executed_transactions': executed_count,
                        'message': 'Заявка успешно создана',
                        'order_id': order.id,
                        'status': order.status,
                        'filled': order.filled_quantity,
                        'remaining': order.quantity - order.filled_quantity
                    }
                    
                    if executed_count > 0:
                        response_data['message'] = f'Заявка создана и исполнено {executed_count} сделок'
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при создании заявки: {e}", exc_info=True)
                return Response(
                    {
                        'error': f'Ошибка при создании заявки: {str(e)}',
                        'code': 'INTERNAL_ERROR'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.warning(f"❌ Ошибка валидации: {serializer.errors}")
        return Response(
            {
                'error': 'Ошибка валидации данных',
                'details': serializer.errors,
                'code': 'VALIDATION_ERROR'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

class CancelOrderView(APIView):
    """Отмена заявки"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        """Отменить заявку пользователя"""
        try:
            with db_transaction.atomic():
                order = Order.objects.select_for_update().get(
                    id=order_id,
                    user=request.user
                )
                
                # Проверяем, можно ли отменить заявку
                if order.status not in ['OPEN', 'PARTIAL']:
                    return Response(
                        {
                            'error': f'Нельзя отменить заявку в статусе {order.get_status_display()}',
                            'code': 'INVALID_STATUS'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # В реальной системе здесь нужно освободить резервы
                # если order_type == 'SELL': освободить зарезервированные скины
                # если order_type == 'BUY': освободить зарезервированные средства
                
                # Отменяем заявку
                old_status = order.status
                order.status = 'CANCELLED'
                order.save()
                
                logger.info(f"✅ Заявка отменена: #{order.id} user={request.user.id}, "
                          f"old_status={old_status}")
                
                return Response({
                    'status': 'success',
                    'message': f'Заявка #{order_id} отменена',
                    'order_id': order_id,
                    'old_status': old_status,
                    'new_status': 'CANCELLED'
                })
                
        except Order.DoesNotExist:
            logger.warning(f"❌ Заявка не найдена: #{order_id} user={request.user.id}")
            return Response(
                {
                    'error': 'Заявка не найдена или у вас нет прав для её отмены',
                    'code': 'ORDER_NOT_FOUND'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при отмене заявки: {e}", exc_info=True)
            return Response(
                {'error': f'Ошибка при отмене заявки: {str(e)}', 'code': 'INTERNAL_ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderListView(ListAPIView):
    """Список заявок"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Показываем заявки текущего пользователя"""
        user = self.request.user
        
        # Фильтрация по типу заявки
        order_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        skin_id = self.request.query_params.get('skin_id')
        
        queryset = Order.objects.filter(user=user).select_related('skin').order_by('-created_at')
        
        if order_type in ['BUY', 'SELL']:
            queryset = queryset.filter(order_type=order_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if skin_id:
            queryset = queryset.filter(skin_id=skin_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Добавляем статистику
        user = request.user
        total_orders = Order.objects.filter(user=user).count()
        open_orders = Order.objects.filter(user=user, status='OPEN').count()
        
        response.data['statistics'] = {
            'total_orders': total_orders,
            'open_orders': open_orders,
            'user_id': user.id,
            'username': user.username
        }
        
        return response

class UserOrderDetailView(RetrieveAPIView):
    """Детали заявки пользователя"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class TransactionListView(ListAPIView):
    """Список транзакций пользователя"""
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Показываем сделки, где пользователь был покупателем или продавцом"""
        user = self.request.user
        
        # Фильтрация
        role = self.request.query_params.get('role')  # buyer или seller
        skin_id = self.request.query_params.get('skin_id')
        
        queryset = Transaction.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('skin', 'buyer', 'seller').order_by('-created_at')
        
        if role == 'buyer':
            queryset = queryset.filter(buyer=user)
        elif role == 'seller':
            queryset = queryset.filter(seller=user)
        
        if skin_id:
            queryset = queryset.filter(skin_id=skin_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Добавляем статистику
        user = request.user
        total_transactions = Transaction.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).count()
        
        bought_transactions = Transaction.objects.filter(buyer=user).count()
        sold_transactions = Transaction.objects.filter(seller=user).count()
        
        response.data['statistics'] = {
            'total_transactions': total_transactions,
            'bought': bought_transactions,
            'sold': sold_transactions,
            'user_id': user.id
        }
        
        return response

class MarketOrderListView(ListAPIView):
    """Рыночные заявки (публичный список)"""
    serializer_class = OrderSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Показываем открытые заявки для конкретного скина"""
        skin_id = self.request.query_params.get('skin_id')
        
        if not skin_id:
            return Order.objects.none()
        
        queryset = Order.objects.filter(
            skin_id=skin_id,
            status__in=['OPEN', 'PARTIAL']
        ).select_related('user', 'skin').order_by('-price')
        
        # Разделяем на покупки и продажи
        order_type = self.request.query_params.get('type')
        if order_type == 'BUY':
            queryset = queryset.filter(order_type='BUY').order_by('-price')
        elif order_type == 'SELL':
            queryset = queryset.filter(order_type='SELL').order_by('price')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Добавляем рыночную информацию
        skin_id = request.query_params.get('skin_id')
        if skin_id:
            # Лучшая цена покупки
            best_buy = Order.objects.filter(
                skin_id=skin_id,
                order_type='BUY',
                status__in=['OPEN', 'PARTIAL']
            ).order_by('-price').first()
            
            # Лучшая цена продажи
            best_sell = Order.objects.filter(
                skin_id=skin_id,
                order_type='SELL',
                status__in=['OPEN', 'PARTIAL']
            ).order_by('price').first()
            
            response.data['market_info'] = {
                'best_bid': float(best_buy.price) if best_buy else None,
                'best_ask': float(best_sell.price) if best_sell else None,
                'spread': float(best_sell.price - best_buy.price) if best_buy and best_sell else None,
                'skin_id': skin_id
            }
        
        return response