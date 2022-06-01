from django.contrib import admin
from .models import *


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'location', 'phone_number', 'subscription', 'paid_until')


class SubscribedEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_added')


admin.site.register(SubscibedEmail, SubscribedEmailAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserFollower)
admin.site.register(Following)
admin.site.register(LoggedUser)
admin.site.register(Notification)
