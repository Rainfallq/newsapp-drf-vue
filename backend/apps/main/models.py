from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class PostManager(models.Manager):
    """Менеджер для модели Post с дополнительными методами"""
    def published(self):
        return self.filter(status='published')

    def pinned_posts(self):
        return self.filter(
            pin_info__isnull=False,
            pin_info__user__subscription__status='active',
            pin_info__user__subscription__end_date__gt=models.functions.Now(),
            status='published'
        ).select_related(
            'pin_info', 'pin_info__user', 'pin_info__user__subscription'
        ).order_by('pin_info__pinned_at')
    
    def regular_posts(self):
        return self.filter(pin_info__isnull=True, status='published')

    def with_subscription_info(self):
        return self.select_related(
            'author', 'author__subscription', 'category'
        ).prefetch_related('pin_info')

    def get_posts_for_feed(self):
        """Возвращает посты для ленты c правильной сортировкой (сначала закрепленные)"""
        return self.with_subscription_info().extra(
            select={
                'is_pinned_order': """
                    CASE WHEN pin_info.id IS NOT NULL 
                         AND pin_info.subscription.status = 'active'
                         AND pin_info.user.subscription.end_date > NOW()
                    THEN 0 ELSE 1 END
                """
            }
        ).order_by('is_pinned_order', '-created_at')


class Post(models.Model):
    """Модель поста с поддержкой закрепления поста"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='published'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveBigIntegerField(default=0)

    objects = PostManager()

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})
    
    @property
    def comments_count(self):
        return self.comments.filter(is_active=True).count()
    
    @property
    def is_pinned(self):
        return hasattr(self, 'pin_info') and self.pin_info is not None   
    
    @property
    def can_be_pinned_by_user(self):
        # Это свойство не должно принимать параметры
        # Логика проверки должна быть вынесена в отдельный метод
        if self.status != 'published':
            return False
        return True
    
    def can_be_pinned_by(self, user):
        if not user or not user.is_authenticated:
            return False
        
        if self.author != user:
            return False
        
        if not hasattr(user, 'subscription') or not user.subscription.is_active:
            return False
        return True
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def get_pinned_info(self):
        if self.is_pinned:
            # Получаем первый объект PinnedPost из RelatedManager
            pinned_post = self.pin_info.first()
            if pinned_post:
                return {
                    'is_pinned': True,
                    'pinned_at': pinned_post.pinned_at,
                    'pinned_by': {
                        'id': pinned_post.user.id,
                        'username': pinned_post.user.username,
                        'has_active_subscription': pinned_post.user.subscription.is_active()
                    }
                }
        return {'is_pinned': False}