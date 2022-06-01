from django import forms
from users.models import SubscibedEmail
from store.models import Vendor, OrderItem
from django.contrib.auth.models import User


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Your First Name',
        'type': 'text',
        'name': 'first_name',
        'id': 'first_name',
        'class': 'form-control'
            }
        )
    )
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Your Username',
        'type': 'text',
        'name': 'username',
        'id': 'username',
        'class': 'form-control'
    }
    )
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Enter Email',
        'type': 'email',
        'name': 'email',
        'id': 'email',
        'class': 'form-control',
            }
        )
    )
    location = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '123 Main Street',
        'type': 'text',
        'name': 'location',
        'id': 'location',
        'class': 'form-control'
            }
        )
    )
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Your Phone Number',
        'type': 'text',
        'name': 'phone_number',
        'id': 'phone_number',
        'class': 'form-control'
            }
        )
    )

    customer_pics = forms.ImageField()

    class Meta:
        model = User
        fields = ['first_name', 'username',
                  'email', 'location', 'phone_number',
                  'customer_pics',
                  ]


class EmailSignupForm(forms.ModelForm):
    email = forms.EmailField(label='', widget=forms.EmailInput(attrs={
        'placeholder': 'Your email',
        'type': 'email',
        'name': 'email',
        'id': 'email',
        'class': 'form-control'
            }
        )
    )

    class Meta:
        model = SubscibedEmail
        fields = ['email']


class StoreCreateForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['vendor_store_name', 'vendor_delivery_method']


class UpdateDeliverStatus(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['status']
