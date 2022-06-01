from django.urls import path
from .views import *

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('post-review/', post_review, name='post-review'),
    path('about/', about, name='about'),
    path('cart/', cart, name='cart'),
    path('update_item/', updateItem, name='update_item'),
    path('update_item/<int:pk>', add_to_cart, name='update_wishlist'),
    path('process_order/', processOrder, name='process_order'),
    path('process_order/now', process_order_view, name='process__order'),
    path('pricing/', pricing_view, name='pricing_view'),
    path('<str:username>/store/', UserProductView.as_view(), name='user-post'),
    path('profile/vendors/', user_followers_product, name='user_followers_product'),
    path('create/product/', product_create_view, name='store-create'),
    path('product/<int:pk>/update/', ProductUpdateView.as_view(), name='store-update'),
    path('product/<int:pk>/delete/', ProductDeleteView.as_view(), name='store-delete'),
    path('notify/', ConfirmNotification.as_view(), name='confirm-notification'),
    path('product/<int:pk>/', store_dynamic_view, name='store-detail'),
    path('product/<int:pk>/remove/', remove_from_cart, name='remove-product'),

    path('api/<int:pk>/add/', ProductAddToCartApi.as_view(), name='like-api'),

    path('api/<str:username>/follow/', ProductFollowApi.as_view(), name='follower-api'),
    # path('api/<str:seller>/add/', ProductFollowApi.as_view(), name='follow-api'),

    path('comment/<int:pk>/', productReview, name='productReview'),

    path('ajax-posting/<int:pk>/', ajax_posting, name='ajax_posting'),  # ajax-posting / name = that we will use in
    # ajax url

]
