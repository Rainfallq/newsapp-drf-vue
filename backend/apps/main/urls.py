from . import views
from django.urls import path


urlpatterns = [
    #Categories
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:category_slug>/posts/', views.post_by_category, name='post-by-category'),

    #Posts
    path('', views.PostListCreateView.as_view(), name='post-list'),
    path('my-posts/', views.MyPostsView.as_view(), name='my-posts'),
    path('popular/', views.popular_posts, name='popular-posts'),
    path('pinned/', views.pinned_posts_only, name='pinned-posts-only'),
    path('recent/', views.recent_posts, name='recent-posts'),
    path('featured/', views.featured_posts, name='featured-posts'),
    path('<slug:slug>/toggle-pin/', views.toggle_post_pinned_status, name='toggle-post-pin'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post-detail'),
]