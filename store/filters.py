import django_filters
from django import forms
from .models import *


class ProductFilter(django_filters.FilterSet):
    # name = django_filters.CharFilter(label='', widget=django_filters.TextInput(attrs={'placeholder': 'Name'}))
    # name = django_filters.CharFilter(label='', wigdget=django_filters.ChoiceFilter(attrs={'placeholder': 'Search'}))
    name = django_filters.Filter(field_name='name', lookup_expr='icontains', label='')

    class Meta:
        model = Product
        fields = [
            'name',
        ]


class ProductPriceFilter(django_filters.FilterSet):
    price = django_filters.AllValuesFilter(field_name='price', lookup_expr='icontains', label='')

    class Meta:
        model = Product
        fields = [
            'price',
        ]
