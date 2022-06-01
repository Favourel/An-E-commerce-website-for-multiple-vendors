from django import forms
from .models import Product, ProductReview
from ckeditor.fields import RichTextFormField, CKEditorWidget
from djrichtextfield import sanitizer


class ProductForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Product Name',
        'type': 'text',
        'name': 'product_name',
        'id': 'product_name',
        'class': 'form-control'
            }
        )
    )
    price = forms.IntegerField(widget=forms.NumberInput(attrs={
        'placeholder': 'Product Price',
        'type': 'number',
        'name': 'price',
        'id': 'product_name',
        'class': 'form-control'
    }
    )
    )
    description = RichTextFormField(widget=forms.Textarea(attrs={
        'placeholder': 'Product Description',
        'type': 'text',
        'name': 'product_description',
        'id': 'product_description',
        'class': 'form-control'
    }
    )
    )

    # seller_delivery_price = forms.IntegerField(widget=forms.NumberInput(attrs={
    #     'placeholder': 'Product Delivery Price',
    #     'type': 'number',
    #     'name': 'seller_delivery_price',
    #     'id': 'seller_delivery_price',
    #     'class': 'form-control'
    #         }
    #     )
    # )
    # category = forms.RegexField(regex=8)

    class Meta:
        model = Product
        exclude = [
            'seller', 'digital', 'date', 'seller_delivery_price', 'order_count'
        ]
