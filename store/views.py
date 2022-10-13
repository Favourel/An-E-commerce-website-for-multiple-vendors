from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View, UpdateView, DeleteView, CreateView, ListView, DetailView
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from .forms import ProductForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from .filters import *
import datetime
import json
from django.http import JsonResponse
from users.models import User, UserFollower, Following, LoggedUser
from users.models import SubscibedEmail
import requests
from users.forms import EmailSignupForm
from .models import *
from users.stripe import *
from djstripe import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.sessions.models import Session

from django.core.mail import EmailMessage, send_mass_mail, send_mail
from django.template.loader import get_template, render_to_string
from django.db.models import F
from django.db.models import Sum
from users.models import Notification

# Create your views here.

MAILCHIMP_API_KEY = settings.MAILCHIMP_API_KEY
MAILCHIMP_DATA_CENTER = settings.MAILCHIMP_DATA_CENTER
MAILCHIMP_EMAIL_LIST_ID = settings.MAILCHIMP_EMAIL_LIST_ID

api_url = f'https://{MAILCHIMP_DATA_CENTER}.api.mailchimp.com/3.0'
members_endpoint = f'{api_url}/list/{MAILCHIMP_EMAIL_LIST_ID}/members'


def subscribe(email):
    data = {
        'email_address': email,
        'status': 'subscribed'
    }
    r = requests.post(
        members_endpoint,
        auth=('', MAILCHIMP_API_KEY),
        data=json.dumps(data)
    )
    return r.status_code, r.json()


class Home(View):
    def get(self, request):
        categories = Category.getAllCategory()
        form = EmailSignupForm()
        return render(request, 'store/home.html', {'categories': categories,
                                                   'form': form,
                                                   })

    def post(self, request):
        form = EmailSignupForm()
        if request.method == 'POST':
            if form.is_valid():
                email_signup_qs = SubscibedEmail.objects.filter(seller=form.instance.email)
                if email_signup_qs.exists():
                    messages.info(request, 'YOU ARE ALREADY SUBSCRIBED.')
                else:
                    subscribe(form.instance.email)
                    form.save()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return render(request, 'store/home.html', {'form': form,
                                                   })


@login_required
def cart(request):
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
        'title': 'Cart',
        'vendor_email_list': vendor_email_list1
    }

    return render(request, 'store/cart.html', context)


class ProductDetail(DetailView):
    models = Product

    def get(self, request, **kwargs):
        object = self.get_object()
        object.count = int(object.count + 1)
        object.save()
        return super(ProductDetail, self).get(self, request, **kwargs)

    def get_queryset(self):
        return Product.objects.all()


def store_dynamic_view(request, pk):
    products = get_object_or_404(Product, pk=pk)
    # Product.objects.filter(name=products.name).update(count=F('count')+1)
    # products.count = (products.count + 1)
    # products.save()
    comments = products.productreview_set.all().order_by('-id')
    seller_products = Product.objects.filter(seller=products.seller).order_by('date_updated').exclude(
        name=products.name)
    category_products = Product.objects.filter(category=products.category).order_by('?').exclude(name=products.name)
    more_products = Product.objects.all().order_by('?').exclude(name=products)

    # user_ = Following.objects.get(current_user=request.user)
    # user_following = [i for i in user_.user_followed.all()]
    # user_following.append(request.user)

    # if request.user.is_authenticated:
    #     vendor = Vendor.objects.get(user=request.user.vendor.user)
    #     vendor_following_products = Product.objects.filter(
    #         seller__in=vendor.vendor_following_list.all()).order_by('-date_updated').exclude(name=products)
    # else:
    #     vendor_following_products = Product.objects.all().order_by('?').exclude(name=products)

    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page')
    comments = paginator.get_page(page_number)

    paginator = Paginator(seller_products, 6)
    page_number = request.GET.get('page')
    seller_products = paginator.get_page(page_number)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']

    if request.method == 'POST':
        if products.seller == request.user:
            products.delete()
        messages.success(request, f'{products} HAS BEEN SUCCESSFULLY DELETED!')
        return redirect(f'../../../{request.user}/store/')

    if request.user.is_authenticated:
        if Vendor.objects.filter(user=request.user).exists():
            notify_orders = OrderItem.objects.filter(
                product__in=request.user.product_set.all()).order_by('-date_added')[:5]
        else:
            notify_orders = {'notify_orders': 0}
    else:
        notify_orders = []

    if request.user.is_authenticated:
        user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]
    else:
        user_followers = []

    if request.user.is_authenticated:
        logged_user = LoggedUser.objects.filter(user__in=request.user.user_following_list.all())
        loggedin_list = [user_.user for user_ in logged_user]
    else:
        logged_user = []
        loggedin_list = []
    online = get_all_logged_in_users()

    context = {
        'user_followers': user_followers,
        'notify_orders': notify_orders,
        'logged_user': logged_user,
        'loogedin_list': loggedin_list,
        "online_list": online,

        'product': products,
        'cartItems': cartItems,
        'seller_products': seller_products,
        'more_products': more_products,
        'comments': comments,
        'category_products': category_products,
        # 'vendor_following_products': vendor_following_products
    }
    return render(request, 'store/product_detail.html', context)


class UserProductView(View):
    def get(self, request, username, *args, **kwargs):
        try:
            categories = Category.getAllCategory().order_by('-id')
            user = get_object_or_404(User, username=username)
            products = Product.objects.filter(seller=user).order_by('id')
            # products = user.product_set.all().order_by('id')
            total_products = products.count()

            myFilter = ProductFilter(request.GET, queryset=products)
            products = myFilter.qs

            myFilterSet = ProductPriceFilter(request.GET, queryset=products)
            products = myFilterSet.qs

            paginator = Paginator(products, 16)
            page_number = request.GET.get('page')
            products = paginator.get_page(page_number)

            host = request.get_host()

            if request.user.is_authenticated:
                customer = request.user
                order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
                items = order.orderitem_set.all()
                cartItems = order.get_cart_items
            else:
                items = []
                order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
                cartItems = order['get_cart_items']

            if request.GET.get('category_id'):
                if request.user.is_authenticated:
                    customer = request.user
                    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
                    items = order.orderitem_set.all()
                    cartItems = order.get_cart_items
                else:
                    items = []
                    order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
                    cartItems = order['get_cart_items']

                user = get_object_or_404(User, username=username)
                host = request.get_host()

                filterProduct = Product.getProductByFilter(request.GET['category_id']).order_by('-id')
                filter_category_product = filterProduct.filter(seller=user).order_by('-id')

                paginator = Paginator(products, 12)
                page_number = request.GET.get('page')
                products = paginator.get_page(page_number)

                # paginator = Paginator(filter_category_product, 1)
                # page_number = request.GET.get('page')
                # filter_category_product = paginator.get_page(page_number)

                # myFilterSet = ProductPriceFilter(request.GET, queryset=filter_category_product)
                # filter_category_product = myFilterSet.qs

                return render(request, 'store/user_post.html', {"products": filter_category_product,
                                                                "categories": categories,
                                                                'cartItems': cartItems,
                                                                'myFilter': myFilter,
                                                                'user': user,
                                                                'host': host,
                                                                'myFilterSet': myFilterSet,
                                                                'total_products': total_products,
                                                                'product': products
                                                                })

            logged_user = LoggedUser.objects.all()
            loggedin_list = [user_.user for user_ in logged_user]

            context = {
                'logged_user': logged_user,
                'loogedin_list': loggedin_list,
                'products': products,
                'items': items,
                'order': order,
                'cartItems': cartItems,
                "categories": categories,
                'myFilter': myFilter,
                'user': user,
                'host': host,
                'myFilterSet': myFilterSet,
                # 'c_count': c_count
                'title': user.vendor.vendor_store_name,
                "total_products": total_products,
            }

            return render(request, 'store/user_post.html', context)

        except ObjectDoesNotExist:
            messages.error(self.request, "NO ACTIVE STORE FOUND")
            return redirect("profile")

            # return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


@login_required
def user_followers_product(request):
    if request.user.user_following_list.all().exists():
        categories = Category.getAllCategory().order_by('-id')
        current_user_ = request.user.user_following_list.all()
        vendor_following_products = Product.objects.filter(
            seller__in=current_user_).order_by('-date_updated')

        top_selling_products = Product.objects.filter(
            seller__in=current_user_).order_by('-order_count')[:10]

        t = Product.objects.filter(orderitem__date_added__lte=datetime.datetime.today(),
                                   orderitem__date_added__gt=datetime.datetime.today() - datetime.timedelta(
                                       days=7)).annotate(
            quantity_sum=Sum('orderitem__quantity')).order_by('-quantity_sum')

        r = datetime.datetime.today() - datetime.timedelta(
                                       days=7)

        labels = []
        data = []
        date_ = []
        # numb = [2, 5, 6, 3, 1, 90]
        #
        # max = numb[0]
        # for number in numb:
        #     if number > max:
        #         max = number
        # print(max)

        for top_product in vendor_following_products:
            labels.append(top_product.name)
            data.append(top_product.orderitem_set.all())
            date_.append(top_product.orderitem_set.count())

        myFilter = ProductFilter(request.GET, queryset=vendor_following_products)
        vendor_following_products = myFilter.qs

        myFilterSet = ProductPriceFilter(request.GET, queryset=vendor_following_products)
        vendor_following_products = myFilterSet.qs

        paginator = Paginator(vendor_following_products, 24)
        page_number = request.GET.get('page')
        vendor_following_products = paginator.get_page(page_number)

        if request.GET.get('category_id'):
            if request.user.is_authenticated:
                customer = request.user
                order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
                items = order.orderitem_set.all()
                cartItems = order.get_cart_items
            else:
                items = []
                order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
                cartItems = order['get_cart_items']

            filterProduct = Product.getProductByFilter(request.GET['category_id']).order_by('-id')
            filter_category_product = filterProduct.filter(seller__in=current_user_).order_by('-id')

            paginator = Paginator(vendor_following_products, 24)
            page_number = request.GET.get('page')
            vendor_following_products = paginator.get_page(page_number)
            top_selling_products = Product.objects.filter(
                seller__in=current_user_).order_by('-order_count')[:10]

            return render(request, 'store/user_followers_store.html',
                          {
                           # 'vendor_following_products': vendor_following_products,
                           'items': items,
                           'order': order,
                           'cartItems': cartItems,
                           'myFilter': myFilter,
                           'myFilterSet': myFilterSet,
                           "top_selling_products": top_selling_products,
                           "vendor_following_products": filter_category_product,
                           "categories": categories,
                           })

        if request.user.is_authenticated:
            customer = request.user
            order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
            items = order.orderitem_set.all().order_by('-id')
            cartItems = order.get_cart_items
        else:
            items = []
            order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
            cartItems = order['get_cart_items']
        context = {
            'vendor_following_products': vendor_following_products,
            'items': items,
            'order': order,
            'cartItems': cartItems,
            'myFilter': myFilter,
            'myFilterSet': myFilterSet,
            "categories": categories,
            'labels': labels,
            'data': data,
            "date_": date_,
            "max": max,
            "top_selling_products": top_selling_products,
            't': t

        }
        return render(request, 'store/user_followers_store.html', context)

    else:
        messages.error(request, "NO ACTIVE STORE FOUND")
        return redirect("profile")


@login_required
def product_create_view(request):
    if request.user.subscription:
        user_plan = models.Plan.objects.filter(product=request.user.subscription.plan.product)
    else:
        user_plan = models.Plan.objects.filter(product=request.user.subscription)

    plan_first = models.Plan.objects.first()
    plan_second = models.Plan.objects.get(pk=2)
    plan_third = models.Plan.objects.get(pk=3)
    products = Product.objects.filter(seller=request.user)
    if request.user.has_paid():
        if request.user.subscription.plan == plan_first:
            if len(products) < 3:
                if request.method == 'POST':
                    form = ProductForm(request.POST, request.FILES)
                    if form.is_valid():
                        form = form.save(commit=False)
                        form.seller = request.user
                        form.save()
                        messages.success(request, f'{form.name} HAS BEEN SUCCESSFULLY UPLOADED!')
                        return redirect(form.get_absolute_url())
                    if request.user in form.seller.follower.all():
                        notification = messages.success(request, f'{form.name} HAS BEEN SUCCESSFULLY UPLOADED!')
                        return render(request, 'users/profile.html', {'notification': notification})
                else:
                    form = ProductForm()
                context = {
                    'form': form
                }
                return render(request, 'store/product_create_form.html', context)
            else:
                for plan in user_plan:
                    messages.info(request, f'You are currently on - {plan.product} plan. Upgrade to have access to '
                                           f'upload more product(s)')
                return redirect('subscription')
        elif request.user.subscription.plan == plan_second:
            if len(products) < 6:
                if request.method == 'POST':
                    form = ProductForm(request.POST, request.FILES)
                    if form.is_valid():
                        form = form.save(commit=False)
                        form.seller = request.user
                        form.save()
                        messages.success(request, f'{form.name} HAS BEEN SUCCESSFULLY UPLOADED!')
                        return redirect(form.get_absolute_url())
                else:
                    form = ProductForm()
                context = {
                    'form': form
                }
                return render(request, 'store/product_create_form.html', context)
            else:
                for plan in user_plan:
                    messages.info(request, f'You are currently on - {plan.product} plan. Upgrade to have access to '
                                           f'upload more product(s)')
                return redirect('subscription')
        elif request.user.subscription.plan == plan_third:
            if len(products) < 7:
                if request.method == 'POST':
                    form = ProductForm(request.POST, request.FILES)
                    if form.is_valid():
                        form = form.save(commit=False)
                        form.seller = request.user
                        form.save()
                        messages.success(request, f'{form.name} HAS BEEN SUCCESSFULLY UPLOADED!')
                        return redirect(form.get_absolute_url())
                else:
                    form = ProductForm()
                context = {
                    'form': form
                }
                return render(request, 'store/product_create_form.html', context)
            else:
                messages.error(request, 'You have reached your limit and can no longer upload product(s).')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'YOU MUST SUBSCRIBE TO UPLOAD PRODUCTS(S).')
        return redirect('subscription')


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    fields = ['category', 'name', 'price', 'description', 'image', 'image2']

    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, f"{form.instance.name} HAS BEEN SUCCESSFULLY UPDATED")
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.seller:
            return True
        return False


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product

    def get_success_url(self):
        post = self.get_object()
        return reverse(f'../../../{post.seller}/store/')

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.seller:
            return True
        return False


class ProductAddToCartApi(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        user = self.request.user
        customer = self.request.user
        product = get_object_or_404(Product, pk=pk)

        updated = False
        liked = False

        if user:
            liked = True
            order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
            orderItem, created = OrderItem.objects.get_or_create(customer=customer, order=order, product=product)
            orderItem.quantity = (orderItem.quantity + 1)
            orderItem.save()
            cartItems = order.get_cart_items
            if orderItem.quantity > 1:
                message = f'"{product}" quantity has been updated!'
            else:
                message = f'"{product}" has been added to your cart!'
            updated = True

            data = {'cartItems': cartItems, 'updated': updated, 'liked': liked,
                    'message': message, 'time': orderItem.date_added
                    }
            return Response(data)

        data = {
            'updated': updated,
            'liked': liked,
            'message': 'Your cart has been updated!',

        }
        return Response(data)


@csrf_protect
def updateItem(request):
    data = json.loads(request.body)
    action = data['action']
    productId = data['productId']
    print('Action:', action)
    print('ProductId:', productId)
    customer = request.user
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(customer=customer, order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
        if orderItem.quantity > 1:
            messages.success(request, f'"{product}" quantity has been increased')
        else:
            messages.success(request, f'"{product}" has been added to your cart')
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
        messages.success(request, f'"{product}" quantity has been reduced')
    orderItem.save()
    if orderItem.quantity <= 0:
        orderItem.delete()
    if action == 'delete':
        orderItem.delete()
        messages.success(request, f"'{product.name}' has been removed from your cart")
    return JsonResponse('Item was added', safe=False)


@csrf_protect
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        order_details = OrderItem.objects.filter(order=order).order_by('-id')
        vendor_email_list1 = list(detail_.product.seller.email for detail_ in order_details)
        for i in order_details:
            vendor_email_list = i.product.seller.email
        host = request.get_host()

        total = float(data['form']['total'])
        order.transaction_id = transaction_id
        if total == float(order.get_cart_total):
            order.complete = True
        order.save()
        notification = Notification.objects.create(main_users=request.user, notification_msg=order, is_read=False)
        notification.save()

        queryset = []
        for let in order.orderitem_set.all():
            queryset.append(let.product.order_count + 1)
            let.product.order_count = (let.product.order_count + 1)
            let.product.save()

        # products.count = (products.count + 1)
        # products.save()
        # .update(count=F('count') + 1)

        template = get_template('store/email_template.html').render(
            {
                # 'price': order_detail.product.price,
                # 'delivery_price': order_detail.product.seller_delivery_price,
                'host': host,
                'user_info': request.user.username,
                'address': request.user.location,
                'order_details': order_details,
                # 'quantity': order_detail.quantity
            }
        )
        email = EmailMessage(
            'THANKS! for purchasing from MyEshop',
            template,
            settings.EMAIL_HOST_USER,
            [vendor_email_list, request.user.email],

        )
        email.fail_silently = False
        email.content_subtype = 'html'
        email.send()

        messages.success(request, 'Your order was successfully placed.')

    else:
        print('User is not logged in...')
    return JsonResponse('Payment complete!', safe=False)


class ConfirmNotification(APIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = self.request.user
        customer = self.request.user
        # order = get_object_or_404(Order, pk=pk)

        updated = False
        read = False

        if user:
            read = True
            order = Order.objects.filter(customer_name=customer, complete=False)
            notify = Notification.objects.get(main_users=customer, notification_msg__in=order, is_read=True)
            notify.save()
            updated = True

            data = {'updated': updated, 'read': read,
                    }
            return Response(data)

        data = {
            'updated': updated,
            'read': read,
            'message': 'Your cart has been updated!',

        }
        return Response(data)


def process_order_view(request):
    transaction_id = datetime.datetime.now().timestamp()
    customer = request.user
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    order_details = OrderItem.objects.filter(order=order).order_by('-id')
    order.transaction_id = transaction_id
    order.complete = True
    order.save()

    vendor_email_list1 = list(detail_.product.seller.email for detail_ in order_details)
    for i in order_details:
        vendor_email_list = i.product.seller.email
    host = request.get_host()

    queryset = []
    for let in order.orderitem_set.all():
        queryset.append(let.product.order_count + 1)
        let.product.order_count = (let.product.order_count + 1)
        let.product.save()

    # products.count = (products.count + 1)
    # products.save()
    # .update(count=F('count') + 1)

    template = get_template('store/email_template.html').render(
        {
            # 'price': order_detail.product.price,
            # 'delivery_price': order_detail.product.seller_delivery_price,
            'host': host,
            'user_info': request.user.username,
            'address': request.user.location,
            'order_details': order_details,
            # 'quantity': order_detail.quantity
        }
    )
    email = EmailMessage(
        'THANKS! for purchasing from MyEshop',
        template,
        settings.EMAIL_HOST_USER,
        [vendor_email_list, request.user.email],

    )
    email.fail_silently = False
    email.content_subtype = 'html'
    email.send()

    messages.success(request, 'Your order was successfully placed.')
    return redirect('customer-orders')


def post_review(request):
    if request.user.is_authenticated:
        customer = request.user
        if request.method == 'POST':
            message = request.POST['message']
            message_subject = request.POST['message_subject']

            review = Review.objects.create(customer_name=customer,
                                           message=message,
                                           message_subject=message_subject)
            review.save()
            messages.info(request, 'Message has been sent!')

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "You have to be logged in to upload comments")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'store/base.html', {})


def remove_from_cart(request, pk):
    customer = request.user
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(customer=customer, order=order, product=product)
    if OrderItem.objects.filter(customer=customer, order=order, product=orderItem.product).exists():
        orderItem.delete()
        messages.success(request, f"'{product.name}' has been removed from your cart")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "Product doesn't exists")
        return redirect('cart')


@login_required
def add_to_cart(request, pk):
    customer = request.user
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(customer=customer, order=order, product=product)
    orderItem.quantity = (orderItem.quantity + 1)
    orderItem.save()
    if orderItem.quantity > 1:
        messages.success(request, f'"{product}" quantity has been updated!')
    else:
        messages.success(request, f'"{product}" has been added to your cart!')
    return redirect('cart')


def about(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']
    online = get_all_logged_in_users()
    if request.user.is_authenticated:
        user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]
    else:
        user_followers = 0
    if request.user.is_authenticated:
        if Vendor.objects.filter(user=request.user).exists():
            notify_orders = OrderItem.objects.filter(
                product__in=request.user.product_set.all()).order_by('-date_added')[:5]
        else:
            notify_orders = {'notify_orders': 0}
    else:
        notify_orders = {'notify_orders': 0}
    context = {
        'user_followers': user_followers,
        'notify_orders': notify_orders,
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'title': 'Checkout',
        'online_list': online
    }
    return render(request, 'store/about.html', context)


def pricing_view(request):
    products = models.Product.objects.all()
    online = get_all_logged_in_users()
    if request.user.is_authenticated:
        user_followers = request.user.userfollower_set.all().order_by('-date_followed')[:4]
    else:
        user_followers = 0
    if request.user.is_authenticated:
        if Vendor.objects.filter(user=request.user).exists():
            notify_orders = OrderItem.objects.filter(
                product__in=request.user.product_set.all()).order_by('-date_added')[:5]
        else:
            notify_orders = {'notify_orders': 0}
    else:
        notify_orders = {'notify_orders': 0}
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer_name=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
        cartItems = order['get_cart_items']
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'products': products,
        'online_list': online,
        'user_followers': user_followers,
        'notify_orders': notify_orders,
    }
    return render(request, 'store/pricing.html', context)


# ajax_posting function
def ajax_posting(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.is_ajax():
        customer_info = request.user
        review = request.POST.get('review', None)  # getting data from first_name input
        response_data = {}

        post = ProductReview(review=review, customer_info=request.user, product=product)
        post.save()

        if review:  # checking if first_name and last_name have value
            response = {
                'msg': 'Your form has been submitted successfully'  # response message
            }
            return JsonResponse(response)  # return response as JSON


def productReview(request, pk):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, pk=pk)
        customer_info = request.user

        if request.method == 'POST':
            review = request.POST['review']
            product_review = ProductReview.objects.create(
                customer_info=customer_info,
                product=product,
                review=review,
            )
            product_review.save()
            # messages.info(request, f"Review has been posted")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "You have to be logged in to upload comments")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'store/product_detail.html', {})


class ProductFollowApi(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username, format=None):
        # pk = self.kwargs.get('pk')
        user = self.request.user
        from users.models import User
        obj = get_object_or_404(User, username=username)

        check = UserFollower.objects.create(user=obj, user_followers=user)
        check_ = UserFollower.objects.filter(user=obj, user_followers=user)

        Vendor.objects.filter(user=user, vendor_follower=obj)
        Vendor.objects.filter(user=user, vendor_following_list=obj)
        is_following = True if UserFollower.objects.filter(user=obj, user_followers=user) else False

        updated = False
        following = False

        if user:
            if user in obj.follower.all():
                following = False
                check_.delete()
                obj.follower.remove(user)
                user.user_following_list.remove(obj)
                obj.vendor.vendor_follower.remove(user)
                if Vendor.objects.filter(user=request.user).exists():
                    Vendor.unfollow(obj, user)
                    Vendor.unfollow_vendor_following_list(user, obj)

                message_user = f'"{user}" unfollowed {obj}'
            else:
                following = True
                check.save()
                obj.follower.add(user)
                user.user_following_list.add(obj)
                obj.vendor.vendor_follower.add(user)

                if Vendor.objects.filter(user=request.user).exists():
                    Vendor.follow(obj, user)
                    Vendor.follow_vendor_following_list(user, obj)
                message_user = f'"{user}" is following {obj}'

                data = {
                    'updated': updated,
                    'follow': following,
                    'message_user': message_user
                }
                return Response(data)

            updated = True

        data = {
            'updated': updated,
            'follow': following,
        }
        return Response(data)


def get_all_logged_in_users():
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return User.objects.filter(id__in=uid_list)

