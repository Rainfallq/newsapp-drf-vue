from django.contrib import admin
from .models import Payment, PaymentAttempt, Refund, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_payment_intent_id', 'stripe_session_id']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    raw_id_fields = ['user', 'subscription']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'subscription', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Stripe данные', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__user__username', 'stripe_charge_id']
    readonly_fields = ['created_at']
    raw_id_fields = ['payment']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'amount', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__user__username', 'stripe_refund_id']
    readonly_fields = ['created_at', 'processed_at']
    raw_id_fields = ['payment', 'created_by']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('payment', 'amount', 'reason', 'status')
        }),
        ('Stripe данные', {
            'fields': ('stripe_refund_id',),
            'classes': ('collapse',)
        }),
        ('Создатель', {
            'fields': ('created_by',),
        }),
        ('Временные метки', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider', 'event_type', 'status', 'created_at']
    list_filter = ['provider', 'event_type', 'status', 'created_at']
    search_fields = ['event_id', 'event_type']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('provider', 'event_id', 'event_type', 'status')
        }),
        ('Данные', {
            'fields': ('data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Webhook события создаются автоматически