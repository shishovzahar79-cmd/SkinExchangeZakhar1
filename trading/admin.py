from django.contrib import admin
from .models import Order, Transaction

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'skin', 'order_type', 'price', 'quantity', 
                   'filled_quantity', 'status', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('user__username', 'skin__name', 'id')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'skin', 'order_type', 'status')
        }),
        ('Цена и количество', {
            'fields': ('price', 'quantity', 'filled_quantity')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'skin', 'price', 'quantity', 'fee', 
                   'buyer', 'seller', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('buyer__username', 'seller__username', 'skin__name', 'id')
    readonly_fields = ('created_at',)
    list_per_page = 50
    
    fieldsets = (
        ('Участники сделки', {
            'fields': ('buyer', 'seller')
        }),
        ('Предмет сделки', {
            'fields': ('skin', 'price', 'quantity', 'fee')
        }),
        ('Связанные заявки', {
            'fields': ('order_buy', 'order_sell')
        }),
        ('Дата', {
            'fields': ('created_at',)
        }),
    )