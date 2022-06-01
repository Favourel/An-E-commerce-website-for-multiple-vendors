from django import template
register = template.Library()


@register.filter(name="multiply")
def multiply(num, num2):
    return num * num2
