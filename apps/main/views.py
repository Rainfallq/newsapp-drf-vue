from rest_framework import generics, status, filters, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Category, Post
from .serializers import (
    CategorySerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer
)
from .permissions import IsAuthorOrReadOnly

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = ['slug']

class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['title', 'created_at', 'updated_at', 'views_count']
    ordering = ['-created_at']

    def get_queryset(self):
    
        queryset = Post.objects.select_related('author', 'category')

        if not self.request.user.is_authenticated: 
            queryset = queryset.filter(status='published')
        else:
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )

        # Проверяем, нужна ли сортировка с учетом закрепленных постов
        ordering = self.request.query_params.get('ordering', '')
        show_pinned_first = not ordering or ordering in ['-created_at', 'created_at']

        if show_pinned_first:
            return Post.get_posts_for_feed().filter(
                Q(status='published') | (
                    Q(author = self.request.user) if self.request.user.is_authenticated else Q()
                )
            )
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        if hasattr(response, 'data') and 'results' in response.data:
            pinned_count = sum(1 for post in response.data['results'] if post.get('is_pinned', False))
            response.data['pinned_count'] = pinned_count

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.select_related('author', 'category')
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = ['slug']

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.method == 'GET':
            instance.increment_view()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
class MyPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'views_count', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(
            author = self.request.user
        ).select_related('author', 'category')
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)

    posts = Post.objects.with_subscription_info().filter(
        category=category,
        status='published'
    )

 # Используем сложную аннотацию для правильной сортировки
    from django.db.models import Case, When, Value, DateTimeField, BooleanField
    from django.utils import timezone

    posts = posts.annotate(
        effective_date = Case(
            When(
                pin_info__isnull='False',
                pin_info__subscription__status='active',
                pin_info__user__subscription__end_date__gt=timezone.now(),
                then = 'pin_info__pinned_at'
            ),
            default='created_at',
            output_field=DateTimeField()
        ),
        is_pinned_flag = Case(
            When(
                pin_info__isnull='False',
                pin_info__subscription__status='active',
                pin_info__user__subscription_end_date__gt=timezone.now(),
                then=Value('True')
            ),
            default=Value('False'),
            output_field=BooleanField()
        )
    ).order_by('-is_pinned_flag', 'effective_date', '-created_at')

    serializer = PostListSerializer(
        posts, 
        many=True, 
        context={'request': request})

    return Response({
        'category': CategorySerializer(category).data,
        'posts': serializer.data,
        'pinned_posts_count': sum(1 for post in serializer.data if post.get('is_pinned', False))
    })
    

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    posts = Post.objects.with_subscription_info().filter(
        status='published',
    ).order_by('-views_count')[:10]

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def pinned_posts_only(request):
    posts = Post.objects.pinned_posts()
    serializer = PostListSerializer(
        posts,
        many=True,
        context={'request': request}
    )
    return Response({
        'count': posts.count(),
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    posts = Post.objects.with_subscription_info().filter(
        status='published'
    ).order_by('-created_at')[:10]

    serializer = PostListSerializer(
        posts, 
        many=True, 
        context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_posts(request):

    from django.utils import timezone
    from datetime import timedelta
#3 last pinned posts
    pinned_posts = Post.objects.pinned_posts()[:3]

#popular posts for a week except pinned ones
    week_ago = timezone.now() - timedelta(days=7)
    popular_posts = Post.objects.with_subscription_info().filter(
        status='published',
        created_at__gte=week_ago
    ).exclude(
        id__in=[post.id for post in pinned_posts]
    ).order_by('-views_count')[:6]
    
    pinned_serializer = PostListSerializer(
        pinned_posts,
        many=True,
        context={'context': request}
    )

    popular_serializer = PostListSerializer(
        popular_posts,
        many=True,
        context={'context': request}
    )

    return Response({
        'pinned_posts': pinned_serializer.data,
        'popular_posts': popular_serializer.data,
        'total_pinned': Post.objects.pinned_posts().count()
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_pinned_status(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user, status='published')

    if not hasattr(request.user, 'subscription') or not request.user.subscription.is_active():
        return Response({
            'error': 'Active subscription needed to be able to pin posts'
        }, status=status.HTTP_403_FORBIDDEN)
    