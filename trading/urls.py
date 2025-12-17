from django.urls import path
from . import views

urlpatterns = [
    path('order/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('order/cancel/<int:order_id>/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
]