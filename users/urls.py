from django.urls import path
from django.conf.urls import url
from users import views as user_views
from store.middlewares import LogoutCheckMiddleware


urlpatterns = [
    path('register/', LogoutCheckMiddleware(user_views.register), name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('profile/create_store/', user_views.create_store, name='create_store'),
    path('profile/create_store/update/', user_views.updateVendorInfo, name='update_store'),
    path('profile/update/', user_views.updateInfo, name='update-info'),
    path('profile/follower/', user_views.user_follower_view, name='user_follower_view'),
    path('profile/customers/', user_views.customer_product_list, name='customer-product-list'),
    path('profile/customer/<int:pk>/', user_views.updateDeliveryStatus, name='update_store_del'),
    path('profile/orders/', user_views.customer_orders, name='customer-orders'),
    path('profile/subscribe/', user_views.subscription, name='subscription'),
    path('profile/payment/', user_views.payment_method, name='payment_method'),
    path('profile/payment/done/', user_views.card, name='card'),
    path('stripe-webhooks/', user_views.stripe_webhooks, name='stripe_webhooks'),

    url(r'^ajax/validate_username/$', user_views.validate_username, name='validate_username'),

    # path('email/subscribe/', user_views.email_list_signup, name='email-subscribe'),
    path('pay/', user_views.payment, name="pay"),  # add this
    path('success/', user_views.subscription_success, name="success"),  # add this
    path('cancel/', user_views.subscription_cancelled, name="subscription_cancelled"),  # add this
    path('config/', user_views.stripe_config),  # new
    path('create-checkout-session/', user_views.create_checkout_session),  # new

]

