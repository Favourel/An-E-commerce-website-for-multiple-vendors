from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.utils import timezone
from django.conf import settings
from ckeditor.fields import RichTextField
from djstripe.models import Customer, Subscription


# Create your models here.

class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.CASCADE)
    vendor_store_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_delivery_method = models.TextField(null=True, blank=True)
    vendor_follower = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='vendor_follower')
    vendor_following_list = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='vendor_following_list')
    date_joined = models.DateTimeField(default=timezone.now)

    @staticmethod
    def follow(current_user, another_account):
        obj, create = Vendor.objects.get_or_create(user=current_user)
        return obj.vendor_follower.add(another_account)

    @staticmethod
    def unfollow(current_user, another_account):
        obj, create = Vendor.objects.get_or_create(user=current_user)
        return obj.vendor_follower.remove(another_account)

    @staticmethod
    def follow_vendor_following_list(current_user, another_account):
        obj, create = Vendor.objects.get_or_create(user=current_user)
        return obj.vendor_following_list.add(another_account)

    @staticmethod
    def unfollow_vendor_following_list(current_user, another_account):
        obj, create = Vendor.objects.get_or_create(user=current_user)
        return obj.vendor_following_list.remove(another_account)

    def __str__(self):
        return str(self.user)


class Category(models.Model):
    name = models.CharField(max_length=70, null=True, blank=True, default='select category')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @staticmethod
    def getAllCategory():
        return Category.objects.all()


class Product(models.Model):
    name = models.CharField(max_length=220, default='Enter product name')
    price = models.FloatField(default=10)
    digital = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = RichTextField()
    image = models.ImageField(
        upload_to='upload/products',
        default='2+placeholder test.png'
    )
    image2 = models.ImageField(
        upload_to='upload/products',
        null=True, blank=True
    )
    date = models.DateTimeField(default=timezone.now)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seller_delivery_price = models.FloatField(null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    # All Product get
    @staticmethod
    def getAllProduct():
        return Product.objects.all()

    # Filter Product By Category
    @staticmethod
    def getProductByFilter(category_id):
        if category_id:
            return Product.objects.filter(category=category_id)
        else:
            return Product.getAllProduct()

    @staticmethod
    def getProductById(productList):
        return Product.objects.filter(id__in=productList)

    def get_absolute_url(self):
        return reverse('store-detail', kwargs={'pk': self.pk})

    @property
    def get_customer_(self):
        customers = self.orderitem_set.all().order_by('-order')[0:2]
        # all_ = ([item.customer.username for item in customers])
        return customers

    def get_api_like_url(self):
        return reverse('like-api', kwargs={'pk': self.pk})

    def get_remove_product_url(self):
        return reverse('remove-product', kwargs={'pk': self.pk})

    def get_add_product_url(self):
        return reverse('update_wishlist', kwargs={'pk': self.pk})


class Order(models.Model):
    customer_name = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    date_ordered = models.DateTimeField(default=timezone.now)
    complete = models.BooleanField(default=False, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True)

    def __str__(self):
        return str(self.customer_name)

    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now=True)
    CATEGORY_CHOICES = (
        ('Pending', 'Pending'),
        ('Delivered', 'Delivered'),
    )
    status = models.CharField(choices=CATEGORY_CHOICES, max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.order)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total


class Review(models.Model):
    customer_name = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    message_subject = models.CharField(max_length=255, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, blank=True, null=True)


class ProductReview(models.Model):
    customer_info = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    review = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f'{self.customer_info.username} comment'


# class Test(models.Model):
#     cust = models.TextField(null=True, blank=True)
