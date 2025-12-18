from django.urls import path
from . import views

urlpatterns = [
    # Создание и управление заявками
    path('order/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('order/cancel/<int:order_id>/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('order/<int:pk>/', views.UserOrderDetailView.as_view(), name='order-detail'),
    
    # Списки заявок пользователя
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/my/', views.OrderListView.as_view(), name='my-orders'),
    
    # Транзакции
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/my/', views.TransactionListView.as_view(), name='my-transactions'),
    
    # Рыночные данные (публичные)
    path('market/orders/', views.MarketOrderListView.as_view(), name='market-orders'),
]