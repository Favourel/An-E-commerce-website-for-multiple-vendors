from store.models import *
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime, date
import datetime
from djstripe.models import Customer, Subscription
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.shortcuts import reverse
from django.utils import timezone


# Create your models here.


class User(AbstractUser):
    paid_until = models.DateField(
        null=True,
        blank=True
    )

    def set_paid_until(self, date_or_timestamp):
        if isinstance(date_or_timestamp, int):
            # input date as timestamp integer
            paid_until = date.fromtimestamp(date_or_timestamp)
        elif isinstance(date_or_timestamp, str):
            # input date as timestamp string
            paid_until = date.fromtimestamp(int(date_or_timestamp))
        else:
            paid_until = date_or_timestamp

        self.paid_until = paid_until
        self.save()

    def has_paid(
            self,
            current_date=datetime.date.today()
    ):
        if self.paid_until is None:
            return False

        return current_date < self.paid_until

    location = models.CharField(max_length=255, default='Enter Your Current Location')
    phone_number = models.CharField(max_length=20, default='+234')
    customer_pics = models.ImageField(default='146-1468479_my-profile-icon-blank-profile-picture-circle-hd.png',
                                      upload_to='images'
                                      )
    follower = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    user_following_list = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='following_list')
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def imageURL(self):
        try:
            url = self.customer_pics.url
        except:
            url = ''
        return url

    def get_follower_api_url(self):
        return reverse('follower-api', kwargs={'username': self.username})


class UserFollower(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_followers = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user_followers',
        on_delete=models.CASCADE, blank=True, null=True
    )
    date_followed = models.DateTimeField(default=timezone.now, db_index=True)

    @property
    def followers_count(self):
        return UserFollower.objects.filter(user=self.user).count()

    @property
    def following_count(self):
        return UserFollower.objects.filter(user_followers=self.user_followers).count()

    def __str__(self):
        return f'{self.user_followers} is following  {self.user}'


User.add_to_class('following', models.ManyToManyField(
    'self', through=UserFollower, related_name='followers', symmetrical=False))


class SubscibedEmail(models.Model):
    email = models.EmailField()
    date_added = models.DateTimeField(auto_now_add=True)


class Following(models.Model):
    current_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='current_user')
    user_followed = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='user_followed')

    @classmethod
    def follow(cls, current_user, another_account):
        obj, create = cls.objects.get_or_create(current_user=current_user)
        obj.user_followed.add(another_account)
        print('followed')

    @classmethod
    def unfollow(cls, current_user, another_account):
        obj, create = cls.objects.get_or_create(current_user=current_user)
        obj.user_followed.remove(another_account)
        print('unfollowed')

    def __str__(self):
        return str(self.current_user)


class Notification(models.Model):
    main_users = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_msg = models.ForeignKey(Order, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    # notification_msgg = models.ManyToManyField(
    #     OrderItem, related_name='notification_msgg'
    # )
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.notification_msg} has placed an order"

    # def get_api_notify_url(self):
    #     return reverse('confirm-notification', kwargs={'pk': self.pk})


class LoggedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    logged_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username

    def login_user(sender, request, user, **kwargs):
        LoggedUser(user=user).save()

    def logout_user(sender, request, user, **kwargs):
        try:
            u = LoggedUser.objects.filter(user=user)
            u.delete()
        except LoggedUser.DoesNotExist:
            pass

    user_logged_in.connect(login_user)
    user_logged_out.connect(logout_user)
