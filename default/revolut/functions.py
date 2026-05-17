from libraries.banking.revolut import Revolut
from default.settings import REVOLUT_API_SECRET_KEY, REVOLUT_API_VERSION, KLT_WEBHOOK_URL

def create_new_webhook(name: str = 'revolutcallback', events: list = None) -> dict:
    """
    Create a new webhook in Revolut for payment notifications.
    
    Returns:
        The response from the Revolut API after creating the webhook.
    """
    revolut = Revolut(secretKey=REVOLUT_API_SECRET_KEY, apiVersion=REVOLUT_API_VERSION)
    webhook = revolut.webhook
    webhook.url = KLT_WEBHOOK_URL + name
    webhook.events = events or ['ORDER_COMPLETED']
    response = webhook.create()
    return response