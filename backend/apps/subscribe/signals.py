from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Subscription, PinnedPost, SubscriptionHistory

@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """
    Логирование событий, связанных с подпиской.
    """
    if created: 
        # Новая подписка
        SubscriptionHistory.objects.create(
            subscription=instance,
            action='created',
            description=f'Subscription created for a plan {instance.plan.name}',
            metadata={'plan_name': instance.plan.name}
        )
    else:
        # Проверяем изменение статуса (если модель сохраняет прошлый статус)
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status and previous_status != instance.status:
            SubscriptionHistory.objects.create(
                subscription=instance,
                action=instance.status,
                description=f'Subscription status changed from {instance._previous_status} to {instance.status}',
                metadata={'old_status': previous_status, 'new_status=': instance.status}
            )
        
@receiver(post_save, sender=PinnedPost)
def pinned_post_post_save(sender, instance, created, **kwargs):
    """
    Создает историю закрепления поста, если у пользователя есть подписка.
    Если подписка неактивна, удаляет закреп.
    """
    user = instance.user

    # Если новый pinned post, но подписка неактивна - удаляем
    if created:
        subscription = getattr(user, 'subscription', None)
        if not subscription or not getattr(subscription, 'is_active', None):
            instance.delete()
            return  
    
    # Записываем в историю
    SubscriptionHistory.objects.create(
        subscription=subscription,
        action='post_pinned',
        description=f'Post {instance.post.title} pinned',
        metadata={
            'post_id': instance.post.id,
            'post_title': instance.post.title,
        }   
    )

@receiver(pre_delete, sender=PinnedPost)
def pinned_post_pre_delete(sender, instance, **kwargs):
    """
    Логирование удаления закрепленного поста (unpinned)
    """
    subscription = getattr(instance.user, 'subscription', None)
    if subscription:
        SubscriptionHistory.objects.create(
            subscription=subscription,
            action='post_unpinned',
            description=f'Post {instance.post.title} has been unpinned',
            metadata={
                'post_id': instance.post.id,
                'post_title': instance.post.title
            }
        )

    # Убираем связь pinned post, если есть
    if hasattr(instance.user, 'pinned_post'):
        instance.user.pinned_post = None,
        instance.user.save(update_fields=['pinned_post'])

