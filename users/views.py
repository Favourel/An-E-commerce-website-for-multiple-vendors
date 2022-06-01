from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import get_template, render_to_string
from django.contrib.auth.decorators import login_required
from store.models import *
from .forms import *
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.conf import settings
from django.contrib.auth.models import auth
import requests
import json
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

import stripe
import logging
from .stripe import *
import djstripe
from djstripe import models
from users.models import User, UserFollower, Following, LoggedUser, Notification
from django.contrib.auth import password_validation
from django.core.paginator import Paginator

from django.utils.dates import WEEKDAYS
import calendar
from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

# Create your views here.
API_KEY = settings.STRIPE_TEST_SECRET_KEY
logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username has been used already')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email has been used already')
                return redirect('register')
            elif len(password1) < 8 and len(password2) < 8:
                messages.error(request, 'Password must contain at least 8 characters')
                return redirect('register')
            elif password1.isdigit() and password2.isdigit():
                messages.error(request, 'Your password can’t be entirely numeric')
                return redirect('register')
            elif password1 and password2 == username:
                messages.error(request, 'Your password can’t be similar to your username')
                return redirect('register')
            elif password1 and password2 == email:
                messages.error(request, 'Your password can’t be similar to your email')
                return redirect('register')
            else:
                user = User.objects.create_user(
                    first_name=first_name,
                    username=username,
                    email=email,
                    password=password1)
                user.save()

                # template = get_template('store/email_template.html').render({'name': username})
                # email = EmailMessage(
                #     'SIGN UP CONFIRMATION FROM MYESHOP TEAM',
                #     template,
                #     settings.EMAIL_HOST_USER,
                #     [email],
                # )
                # email.fail_silently = False
                # email.content_subtype = 'html'
                # email.send()
                user_login = auth.authenticate(username=username, password=password1)
                auth.login(request, user_login)

                messages.success(request, f'Account created for {username}.')
                return redirect('profile')
        else:
            messages.error(request, 'Passwords are not matching!')
            return redirect('register')
    else:
        return render(request, 'users/register.html', {})


def validate_username(request):
    username = request.GET.get('username', None)
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists(),
        'is_taken_email': User.objects.filter(email__iexact=email).exists(),
    }
    return JsonResponse(data)


@login_required
def profile(request):
    if Vendor.objects.filter(user=request.user).exists():
        products = Product.objects.filter(seller=request.user)
    else:
        products = {'products': 0}

    if Vendor.objects.filter(user=request.user).exists():
        best_selling_products = Product.objects.filter(seller=request.user).order_by('-order_count')[:5]
    else:
        best_selling_products = {'best_selling_products': 0}

    if Vendor.objects.filter(user=request.user).exists():
        notify_orders = OrderItem.objects.filter(
            product__in=request.user.product_set.all()).order_by('-date_added')[:5]
    else:
        notify_orders = {'notify_orders': 0}

    if Vendor.objects.filter(user=request.user).exists():
        total_product = products.count()
    else:
        total_product = 0
    order = OrderItem.objects.filter(customer=request.user)
    total_order = order.count()
    customer = request.user
    orders = OrderItem.objects.filter(customer=customer).order_by('-date_added')
    host = request.get_host()

    followers_ = request.user.follower.all()
    user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]

    user_followers_list = request.user.userfollower_set.all().order_by('-date_followed')
    user_followers_list_count = user_followers_list.count()
    user_following = UserFollower.objects.filter(user_followers=request.user).order_by('-date_followed')
    user_following_count = user_following.count()

    paginator = Paginator(user_following, 6)
    page_number = request.GET.get('page')
    user_following = paginator.get_page(page_number)

    if Vendor.objects.filter(user=request.user).exists():
        current_user_ = Vendor.objects.get(user=request.user,
                                             )
        vendor_following_list__in = current_user_.vendor_following_list.all()
        vendor_following_products = Product.objects.filter(
            seller__in=vendor_following_list__in).order_by('?')[:6]
        notifications = Notification.objects.filter(main_users=request.user)

    else:
        vendor_following_products = Product.objects.filter(
            seller__in=request.user.user_following_list.all()).order_by('?')[:6]
        notifications = {'notifications': 0}

    # order = get_object_or_404(Order, pk=pk)

    paginator = Paginator(user_followers_list, 6)
    page_number = request.GET.get('page')
    user_followers_list = paginator.get_page(page_number)

    labels = []
    data = []

    queryset = Product.objects.order_by('?')[:5]
    for city in queryset:
        labels.append(city.name)
        data.append(city.id)

    paginator = Paginator(orders, 2)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']

    if request.user.subscription:
        user_plan = models.Plan.objects.filter(product=request.user.subscription.plan.product)
    else:
        user_plan = models.Plan.objects.filter(product=request.user.subscription)

    days = {
        '1': _('Monday'),
        '2': _('Tuesday'),
        '3': _('Wednesday'),
        '4': _('Thursday'),
        '5': _('Friday'),
        '6': _('Saturday'),
        '7': _('Sunday')
    }

    DOW_CHOICES = []

    today = datetime.today()
    for i in range(7):
        day_number = (today + timedelta(days=i)).isoweekday()
        day = days[str(day_number)]
        DOW_CHOICES.append(day)
        # print(timedelta(days=i))
        # # print(day_number)
        # print(day)
        # print(DOW_CHOICES)
        # print(today)
    my_model = orders
    # number of items on each page
    number_of_item = 3
    # Paginator
    paginatorr = Paginator(my_model, number_of_item)
    # query_set for first page
    first_page = paginatorr.page(1).object_list
    # range of page ex range(1, 3)
    page_range = paginatorr.page_range

    #
    if request.method == 'POST':
        page_n = request.POST.get('page_n', None)  # getting page number
        results = list(paginatorr.page(page_n).object_list('orderitem_id', 'orderitem_date_added'))
        return JsonResponse({"results": results})

    from store.views import get_all_logged_in_users
    users = User.objects.all()
    online = get_all_logged_in_users()

    logged_user = LoggedUser.objects.filter(user__in=request.user.user_following_list.all())
    loggedin_list = [user_.user for user_ in logged_user]

    context = {
        'order': order,
        'notifications': notifications,
        'logged_user': logged_user,
        'loogedin_list': loggedin_list,
        'user_plan': user_plan,
        'total_product': total_product,
        'total_order': total_order,

        'best_selling_products': best_selling_products,
        'products': products,
        'orders': orders,
        'cartItems': cartItems,
        'host': host,
        'labels': labels,
        'data': data,
        'DOW_CHOICES': DOW_CHOICES,

        'paginatorr': paginatorr,
        'first_page': first_page,
        'page_range': page_range,
        'followers_': followers_,
        'user_followers': user_followers,

        'user_following': user_following,
        'user_following_count': user_following_count,
        'user_followers_list': user_followers_list,
        'user_followers_list_count': user_followers_list_count,
        'notify_orders': notify_orders,
        'users_list': users,
        'online_list': online,
        'vendor_following_products': vendor_following_products
    }
    return render(request, 'users/profile.html', context)


@login_required
def create_store(request):
    user = request.user
    if not Vendor.objects.filter(user=request.user).exists():
        if request.method == 'POST':
            u_form = StoreCreateForm(request.POST)

            if u_form.is_valid():
                u_form = u_form.save(commit=False)
                u_form.user = request.user
                u_form.save()
                store_name = u_form.vendor_store_name
                messages.success(request, f'{store_name} Store has been created by {user}.')
                return redirect('subscription')
        else:
            u_form = StoreCreateForm()

        context = {
            'u_form': u_form,
        }
        return render(request, 'users/create_store.html', context)
    else:
        messages.warning(request, 'You already have a store')
        return redirect('profile')


@login_required
def updateVendorInfo(request):
    try:
        if request.method == 'POST':
            u_form = StoreCreateForm(request.POST, request.FILES, instance=request.user.vendor)

            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Your store has been updated!')
                return redirect(f'../../../{request.user.username}/store/')
        else:
            u_form = StoreCreateForm(instance=request.user.vendor)

        context = {
            'u_form': u_form,
        }
    except ObjectDoesNotExist:
        messages.warning(request, "You do not have an active store")
        return redirect("profile")
    return render(request, 'users/create_store.html', context)


@login_required
def customer_orders(request):
    customer = request.user
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    cartItems = order.get_cart_items
    orders = OrderItem.objects.filter(customer=customer).order_by('-date_added')
    context = {
        'cartItems': cartItems,
        'orders': orders
    }
    return render(request, 'users/user_orders.html', context)


@login_required
def updateInfo(request):
    customer = request.user
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    cartItems = order.get_cart_items
    host = request.get_host()

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)

        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your account has been updated!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            #i changed the error popup
            messages.warning(request, 'error')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        u_form = UserUpdateForm(instance=request.user)

    if Vendor.objects.filter(user=request.user).exists():
        notify_orders = OrderItem.objects.filter(product__in=request.user.product_set.all()).order_by(
            '-date_added')[:4]
    else:
        notify_orders = {'notify_orders': 0}

    user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]

    logged_user = LoggedUser.objects.filter(user__in=request.user.user_following_list.all())
    loggedin_list = [user_.user for user_ in logged_user]

    context = {
        'user_followers': user_followers,
        'notify_orders': notify_orders,
        'logged_user': logged_user,
        'loogedin_list': loggedin_list,

        'host': host,
        'u_form': u_form,
        'cartItems': cartItems,
    }
    return render(request, 'users/update_info.html', context)


@login_required
def customer_product_list(request):
    products = Product.objects.filter(seller=request.user).order_by('-id')
    if Vendor.objects.filter(user=request.user).exists():
        notify_orders = OrderItem.objects.filter(
            product__in=request.user.product_set.all()).order_by('-date_added')[:5]
    else:
        notify_orders = {'notify_orders': 0}

    total_product = products.count()
    orders = OrderItem.objects.filter(product=products).order_by('-date_added')
    customers_orders = OrderItem.objects.filter(product__in=request.user.product_set.all()).order_by(
        '-date_added')
    if request.user.is_authenticated:
        user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]
    else:
        user_followers = 0

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = OrderItem.objects.filter(order=order)
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']

    context = {
        'customers_orders': customers_orders,
        "notify_orders": notify_orders,
        "user_followers": user_followers,
        'products': products,
        'cartItems': cartItems,
        'total_product': total_product,
        'orders': orders,
        'items': items,
    }
    return render(request, 'users/customer_product_list.html', context)


@login_required
def updateDeliveryStatus(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if order.product.seller == request.user:
        if request.method == 'POST':
            u_form = UpdateDeliverStatus(request.POST, instance=order)

            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Status updated!')
                return redirect('customer-product-list')
        else:
            u_form = UpdateDeliverStatus(instance=order)

        context = {'u_form': u_form}
        return render(request, 'users/create_store.html', context)
    else:
        messages.error(request, 'Error!! You are not allowed to!')
        return redirect('profile')


@login_required
def user_follower_view(request):
    followers_ = request.user.follower.all()

    user_followers_list = request.user.userfollower_set.all().order_by('-date_followed')
    user_followers_list_count = user_followers_list.count()
    user_following = UserFollower.objects.filter(user_followers=request.user).order_by('-date_followed')
    user_following_count = user_following.count()

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = order.orderitem_set.all().order_by('-id')
        items_ = OrderItem.objects.filter(order=order)
        cartItems = order.get_cart_items
        vendor_email_list1 = [detail_.product.seller.email for detail_ in items]
        for i in items_:
            vendor_email_list = i.product
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']

    logged_user = LoggedUser.objects.filter(user__in=request.user.user_following_list.all())
    loggedin_list = [user_.user for user_ in logged_user]

    from store.views import get_all_logged_in_users
    online = get_all_logged_in_users()

    user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]
    if Vendor.objects.filter(user=request.user).exists():
        notify_orders = OrderItem.objects.filter(
            product__in=request.user.product_set.all()).order_by('-date_added')[:5]
    else:
        notify_orders = {'notify_orders': 0}

    context = {
        'user_followers': user_followers,
        'notify_orders': notify_orders,
        'logged_user': logged_user,
        'loogedin_list': loggedin_list,
        "online_list": online,

        'items': items,
        'order': order,
        'cartItems': cartItems,
        'followers_': followers_,

        'user_following': user_following,
        'user_following_count': user_following_count,
        'user_followers_list': user_followers_list,
        'user_followers_list_count': user_followers_list_count,

    }
    return render(request, 'users/user_followers.html', context)


@login_required
def subscription(request):
    products = models.Product.objects.all()
    logger.info("subscription")
    return render(request, 'users/subscription_form.html', {'products': products})


@require_POST
@login_required
def payment_method(request):
    stripe.api_key = API_KEY
    plan = request.POST.get('plan', 'm')
    automatic = request.POST.get('automatic', 'on')
    payment_method = request.POST.get('payment_method', 'card')
    context = {}

    plan_inst = SubscriptionPlan(plan_id=plan)
    #               plan_inst.amount
    # 'a' | 'm' =>  plan_inst.currency
    #               plan_inst.stripe_plan_id

    payment_intent = stripe.PaymentIntent.create(
        amount=plan_inst.amount,
        currency=plan_inst.currency,
        payment_method_types=['card']
    )

    if payment_method == 'card':
        context['secret_key'] = payment_intent.client_secret
        context['STRIPE_PUBLISHABLE_KEY'] = settings.STRIPE_TEST_PUBLIC_KEY
        context['customer_email'] = request.user.email
        context['payment_intent_id'] = payment_intent.id
        context['automatic'] = automatic
        context['stripe_plan_id'] = plan_inst.stripe_plan_id

        context['amount'] = plan_inst.amount
        context['currency'] = plan_inst.currency
        context['name'] = plan_inst.name

        return render(request, 'users/card.html', context)


@login_required
def card(request):
    try:
        payment_intent_id = request.POST['payment_intent_id']
        payment_method_id = request.POST['payment_method_id']
        stripe_plan_id = request.POST['stripe_plan_id']
        automatic = request.POST['automatic']
        stripe.api_key = API_KEY

        payment_method_obj = stripe.PaymentMethod.retrieve(payment_method_id)
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method_obj)

        if automatic == 'on':
            # create subs
            customer = stripe.Customer.create(
                email=request.user.email,
                payment_method=payment_method_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )

            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)

            s = stripe.Subscription.create(
                customer=customer.id,
                cancel_at_period_end=True,
                items=[
                    {
                        'plan': stripe_plan_id
                    },
                ]
            )
            stripe.PaymentIntent.modify(
                payment_intent_id,
                payment_method=payment_method_id,
                customer=customer.id
            )

            ret = stripe.PaymentIntent.confirm(
                payment_intent_id
            )

            latest_invoice = stripe.Invoice.retrieve(s.latest_invoice)

            if ret.status == 'requires_action':
                pi = stripe.PaymentIntent.retrieve(
                    latest_invoice.payment_intent
                )
                context = {}

                context['payment_intent_secret'] = pi.client_secret
                context['STRIPE_PUBLISHABLE_KEY'] = settings.STRIPE_TEST_PUBLIC_KEY

                # payload = request.body
                # sig_header = request.META['HTTP_STRIPE_SIGNATURE']
                # event = stripe.Webhook.construct_event(
                #     payload, sig_header, settings.STRIPE_WEBHOOK_SIGNING_KEY
                # )
                # if event.type == 'charge.succeeded':
                #     djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
                #
                #     djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(s)
                #
                #     request.user.customer = djstripe_customer
                #     request.user.subscription = djstripe_subscription
                #     request.user.save()

                return render(request, 'users/3dsec.html', context)

            djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(s)

            vendor_info = Vendor.objects.get(user=request.user)

            request.user.customer = djstripe_customer
            request.user.subscription = djstripe_subscription
            request.user.vendor.subscription = djstripe_subscription
            request.user.save()
            request.user.vendor.save()
            request.user.vendor.subscription.save()

        else:
            stripe.PaymentIntent.modify(
                payment_intent_id,
                payment_method=payment_method_id
            )

            ret = stripe.PaymentIntent.confirm(
                payment_intent_id
            )

            if ret.status == 'requires_action':
                pi = stripe.PaymentIntent.retrieve(
                    payment_intent_id
                )
                context = {}

                context['payment_intent_secret'] = pi.client_secret
                context['STRIPE_PUBLISHABLE_KEY'] = settings.STRIPE_TEST_PUBLIC_KEY

                return render(request, 'users/3dsec.html', context)

        return render(request, 'users/payment_done.html')

    except stripe.error.CardError as e:
        body = e.json_body
        err = body.get('error', {})
        messages.warning(request, f"{err.get('message')}")
        return redirect("profile")

    except stripe.error.RateLimitError as e:
        # Too many requests made to the   too quickly
        messages.warning(request, "Rate limit error")
        return redirect("/")

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        print(e)
        messages.warning(request, "Invalid parameters")
        return redirect("profile")

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        messages.warning(request, "Not authenticated")
        return redirect("profile")

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        messages.warning(request, "Network error")
        return redirect("profile")

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        messages.warning(
            request, "Something went wrong. You were not charged. Please try again.")
        return redirect("profile")

    except Exception as e:
        # send an email to ourselves
        messages.warning(
            request, "A serious error occurred. We have been notified.")
        return redirect("profile")


@require_POST
@csrf_exempt
def stripe_webhooks(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SIGNING_KEY
        )
        logger.info("Event constructed correctly")
    except ValueError:
        # Invalid payload
        logger.warning("Invalid Payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.warning("Invalid signature")
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'charge.succeeded':
        # object has  payment_intent attr
        # pi = stripe.PaymentIntent.retrieve(event.data.object.payment_intent)
        #
        # if pi.customer:
        #     customer = stripe.Customer.retrieve(pi.customer)
        #     email = customer.email
        #
        #     if customer:
        #         subscr = stripe.Subscription.retrieve(
        #             customer['subscriptions'].data[0].id
        #         )
        #         subscription_id = subscr['id']
        #
        #         djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(subscription_id)
        #         request.user.subscription = djstripe_subscription
        #         request.user.save()

        set_paid_until(event.data.object)
        session = event.data.object
        # session_ = stripe.checkout.Session.retrieve(request.GET['session_id'])
        # stripe_subscription_id = session_.subscription
        # djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(stripe_subscription_id)
        # request.user.subscription = djstripe_subscription
        # request.user.save()
    return HttpResponse(status=200)


#
# MAILCHIMP_API_KEY = settings.MAILCHIMP_API_KEY
# MAILCHIMP_DATA_CENTER = settings.MAILCHIMP_DATA_CENTER
# MAILCHIMP_EMAIL_LIST_ID = settings.MAILCHIMP_EMAIL_LIST_ID
#
# api_url = f'https://{MAILCHIMP_DATA_CENTER}.api.mailchimp.com/3.0'
# members_endpoint = f'{api_url}/list/{MAILCHIMP_EMAIL_LIST_ID}/members'
#
#
# def subscribe(email):
#     data = {
#         'email_address': email,
#         'status': 'subscribed'
#     }
#     r = requests.post(
#         members_endpoint,
#         auth=('', MAILCHIMP_API_KEY),
#         data=json.dumps(data)
#     )
#     return r.status_code, r.json()

#
# def email_list_signup(request):
#     form = EmailSignupForm()
#     if request.method == 'POST':
#         if form.is_valid():
#             email_signup_qs = SubscibedEmail.objects.filter(seller=form.instance.email)
#             if email_signup_qs.exists():
#                 messages.info(request, 'You are already subscribed.')
#             else:
#                 subscribe(form.instance.email)
#                 form.save()
#
#         return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@csrf_protect
def cancel(request):
    if request.user.is_authenticated:
        data = request.user.subscription.id
        stripe.api_key = API_KEY
        try:
            stripe.Subscription.delete(data)
        except Exception as e:
            return JsonResponse({'error': (e.args[0])}, status=403)

    return redirect("main:homepage")


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_TEST_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)


def create_checkout_session(request):
    host = request.get_host()
    data = json.loads(request.body)
    user = request.user.email
    # if request.method == 'POST':
    domain_url = 'http://localhost:8000/'
    stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user,
            client_reference_id=request.user.id if request.user.is_authenticated else None,
            success_url='http://127.0.0.1:8000/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://{}{}'.format(host, reverse('profile')),
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price': data['price_Id'],
                    'quantity': 1,
                }
            ],
            # subscription_data=[
            #     {'cancel_at_period_end': True}
            # ],
            # cancel_at_period_end=True,
        )
        return JsonResponse({'sessionId': checkout_session['id']})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required
def subscription_success(request):
    # stripe.api_key = API_KEY
    # pi = stripe.PaymentIntent.retrieve(charge.payment_intent)
    #
    # if pi.customer:
    #     customer = stripe.Customer.retrieve(pi.customer)
    #     email = customer.email
    #
    #     if customer:
    #         subscr = stripe.Subscription.retrieve(
    #             customer['subscriptions'].data[0].id
    #         )
    #         subscription_id = subscr['subscription_id']
    id = request.GET('sessionId')
    checkout_session = stripe.checkout.Session.retrieve(id)
    if request.method == 'GET' and 'session_id' in request.GET:
        session_ = stripe.checkout.Session.retrieve(request.GET['session_id'])
        # session_ = stripe.checkout.Session.retrieve(request.GET['sessionId'])
        stripe_subscription_id = session_.subscription
        djstripe_subscription = djstripe.models.billing.Subscription.sync_from_stripe_data(stripe_subscription_id)
        request.user.subscription = djstripe_subscription
        request.user.save()
    return render(request, 'users/payment_done.html')


@login_required
def subscription_cancelled(request):
    return render(request, 'users/payment_cancelled.html')


@login_required
def payment(request):
    customer = request.user
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    cartItems = order.get_cart_items
    products = models.Product.objects.all()
    context = {
        'products': products,
        'cartItems': cartItems
    }
    return render(request, 'store/pay.html', context)
