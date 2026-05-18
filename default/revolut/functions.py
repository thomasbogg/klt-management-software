from default.settings import REVOLUT_API_SECRET_KEY, REVOLUT_API_VERSION, KLT_WEBHOOK_URL
from libraries.banking.revolut import Revolut
from libraries.utils import log


def create_new_webhook(name: str = 'revolutcallback', events: list = None) -> Revolut.Webhook:
    """
    Create a new webhook in Revolut for payment notifications.
    
    Returns:
        The Revolut webhook object after creating the webhook.
    """
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    webhook = revolut.webhook
    webhook.url = KLT_WEBHOOK_URL + name
    webhook.events = events or ['ORDER_COMPLETED']
    webhook.create()
    return webhook


def delete_webhook(webhookId: str) -> Revolut.Webhook:
    """
    Delete an existing webhook in Revolut by its ID.
    
    Args:
        webhookId: The ID of the webhook to delete.
    Returns:
        The Revolut webhook object after attempting deletion.
    """
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    webhook = revolut.webhook
    webhook.id = webhookId
    deleted = webhook.delete()
    if deleted:
        log(f"Webhook with ID {webhookId} deleted successfully.")
    return webhook


def get_webhooks() -> list[Revolut.Webhook]:
    """
    Retrieve all webhooks from Revolut.
    
    Returns:
        A list of Revolut webhook objects.
    """
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    webhooks = revolut.webhook.list()
    return webhooks


def cancel_payment(orderId: str) -> Revolut.Payment:
    """
    Cancel a payment in Revolut by its order ID.
    
    Args:
        orderId: The ID of the order/payment to cancel.
    Returns:
        The Revolut payment object after attempting cancellation.
    """
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    payment = revolut.payment
    payment.id = orderId
    payment.cancel()
    if payment.state == 'cancelled':
        log(f"Payment with order ID {orderId} cancelled successfully.")
    return payment


def create_dummy_payment(amount: int = 1000, currency: str = 'EUR') -> Revolut.Payment:
    """
    Create a dummy payment in Revolut for testing purposes.
    
    Args:
        amount: The amount of the payment in minor units (e.g., cents).
        currency: The currency code (default is 'EUR').
    Returns:
        The Revolut payment object after creating the dummy payment.
    """
    from default.settings import DEFAULT_ACCOUNT
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    payment = revolut.payment
    payment.customerName = DEFAULT_ACCOUNT.name
    payment.customerEmail = DEFAULT_ACCOUNT.email
    payment.amount = amount
    payment.currency = currency
    payment.description = "Dummy payment for testing"
    payment.create()
    return payment