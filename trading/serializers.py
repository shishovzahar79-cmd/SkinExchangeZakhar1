from rest_framework import serializers
from .models import Order, Transaction
from catalog.serializers import SkinSerializer

class OrderSerializer(serializers.ModelSerializer):
    skin_details = SkinSerializer(source='skin', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_username', 'skin', 'skin_details',
            'order_type', 'price', 'quantity', 'filled_quantity',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'filled_quantity', 'status', 'created_at', 'updated_at']
        extra_kwargs = {
            'skin': {'write_only': True}
        }

class TransactionSerializer(serializers.ModelSerializer):
    skin_details = SkinSerializer(source='skin', read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'buyer', 'buyer_username', 'seller', 'seller_username',
            'skin', 'skin_details', 'price', 'quantity', 'fee',
            'created_at'
        ]