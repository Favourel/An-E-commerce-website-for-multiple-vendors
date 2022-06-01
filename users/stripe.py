import logging
import stripe
from users.models import User

from django.conf import settings

STANDARD = 's'
PREMIUM = 'p'
ENTERPRISE = 'e'

API_KEY = settings.STRIPE_TEST_SECRET_KEY
logger = logging.getLogger(__name__)


class SubscriptionMonthPlanStandard:
    def __init__(self):
        self.name = 'Monthly Vendor Subscription Service (Standard)'
        self.stripe_plan_id = settings.STRIPE_PLAN_MONTHLY_STANDARD_ID
        self.amount = 500000


class SubscriptionMonthPlanPremium:
    def __init__(self):
        self.name = 'Monthly Vendor Subscription Service (Premium)'
        self.stripe_plan_id = settings.STRIPE_PLAN_MONTHLY_PREMIUM_ID
        self.amount = 1000000


class SubscriptionMonthPlanEnterprise:
    def __init__(self):
        self.name = 'Monthly Vendor Subscription Service (Enterprise)'
        self.stripe_plan_id = settings.STRIPE_PLAN_MONTHLY_ENTERPRISE_ID
        self.amount = 2000000


class SubscriptionPlan:
    def __init__(self, plan_id):
        """
        plan_id is either string 'e' (stands for standard)
        or a string letter 'a' (which stands for premium) or 'e' string letter for enterprise
        """
        if plan_id == STANDARD:
            self.plan = SubscriptionMonthPlanStandard()
            self.id = STANDARD
        elif plan_id == PREMIUM:
            self.plan = SubscriptionMonthPlanPremium()
            self.id = PREMIUM
        elif plan_id == ENTERPRISE:
            self.plan = SubscriptionMonthPlanEnterprise()
            self.id = ENTERPRISE
        else:
            raise ValueError('Invalid plan_id value')

        self.currency = 'ngn'

    @property
    def stripe_plan_id(self):
        return self.plan.stripe_plan_id

    @property
    def amount(self):
        return self.plan.amount

    @property
    def name(self):
        return self.plan.name


def set_paid_until(charge):
    logger.info(f"set_paid_until with {charge}")

    stripe.api_key = API_KEY
    pi = stripe.PaymentIntent.retrieve(charge.payment_intent)

    if pi.customer:
        customer = stripe.Customer.retrieve(pi.customer)
        email = customer.email

        if customer:
            subscr = stripe.Subscription.retrieve(
                customer['subscriptions'].data[0].id
            )
            current_period_end = subscr['current_period_end']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(
                f"User with email {email} not found"
            )
            return False

        user.set_paid_until(current_period_end)
        logger.info(
            f"Profile with {current_period_end} saved for user {email}"
        )
    else:
        pass
        # charge.amount  1990 | 19995
        # this was one time payment, update
        # paid_until (e.g. paid_until = current_date + 31 days) using
        # charge.paid + charge.amount attrs