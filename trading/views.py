from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Order, Transaction
from .serializers import OrderSerializer, TransactionSerializer
from .matching_engine import MatchingEngine

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(APIView):
    permission_classes = []
    
    def post(self, request):
        """Создать заявку на покупку/продажу"""
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            # Сохраняем заявку
            order = serializer.save(user=request.user)
            
            # Запускаем движок совпадения для этого скина
            transactions = MatchingEngine.match_orders(order.skin_id)
            
            # Обновляем данные ордера после матчинга
            order.refresh_from_db()
            
            return Response({
                'order': OrderSerializer(order).data,
                'executed_transactions': len(transactions),
                'message': f'Создана заявка на {order.order_type.lower()}'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CancelOrderView(APIView):
    permission_classes = []
    
    def post(self, request, order_id):
        """Отменить заявку"""
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.status == 'OPEN':
                order.status = 'CANCELLED'
                order.save()
                return Response({
                    'status': 'success',
                    'message': f'Заявка #{order_id} отменена'
                })
            return Response(
                {
                    'status': 'error',
                    'message': f'Невозможно отменить заявку в статусе {order.status}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Order.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Заявка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

class OrderListView(ListAPIView):
    permission_classes = []
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """Показываем только заявки текущего пользователя"""
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class TransactionListView(ListAPIView):
    permission_classes = []
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        """Показываем сделки пользователя (как покупателя и продавца)"""
        user = self.request.user
        return Transaction.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).order_by('-created_at')

# Дополнительная функция для тестирования (если нужно)
def test_api(request):
    """Тестовый эндпоинт для проверки API"""
    from django.http import JsonResponse
    return JsonResponse({'message': 'API работает!', 'status': 'ok'})