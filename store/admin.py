from django.contrib import admin
from .models import *
# Register your models here.


class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'date_ordered', 'complete']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'order', 'quantity', 'date_added')


class CommentInline(admin.TabularInline):
    model = ProductReview
# class ShippingAddressAdmin(admin.ModelAdmin):
    # list_display = ('address', 'order', 'date_added')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'order_count', 'category', 'date', 'date_updated')
    list_filter = ('seller', 'date')
    search_fields = ['name', 'price',]
    inlines = [CommentInline]


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'message', 'message_subject', 'date_added')


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['date_added']


admin.site.register(Vendor)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
# admin.site.register(ShippingAddress, ShippingAddressAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ProductReview)
# admin.site.register(Test)

