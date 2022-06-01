from django import template
from store.views import get_all_logged_in_users
register = template.Library()


@register.inclusion_tag('users/profile.html')
def render_logged_in_user_list():
    return {'logged_users': get_all_logged_in_users()}
