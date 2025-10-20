from django.urls import path
from . import views

urlpatterns = [
    #Subscription plan urls
    path('plans/', views.SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('plans/<int:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),

    #User subscriptions
    path('user-subscription/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('status/', views.subscription_status, name='subscription-status'),
    path('history/', views.SubscriptionHistoryView.as_view(), name='subscription-history'),
    path('cancel/', views.cancel_subscription, name='cancel-subscription'),

    #Pinned Posts
    path('pinned-post/', views.PinnedPostView.as_view(), name='pinned-post'),
    path('pin-post/', views.pin_post, name='pin-post'),
    path('unpin-post/', views.unpin_post, name='unpin-post'),
    path('pinned-posts-list/', views.pinned_posts_list, name='pinned-posts-list'),
    path('can-pin/<int:post_id>/', views.can_pin_post, name='can-pin-post'),
]   