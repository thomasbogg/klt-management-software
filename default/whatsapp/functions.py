import os
from correspondence.self.functions import new_email_to_self, send_email_to_self
from default.settings import BROWSER_DIR, DEFAULT_ACCOUNT, BROWSER_USER_DATA_DIR
from web.whatsapp import BrowseWhatsApp


def login_to_whatsapp() -> BrowseWhatsApp:
    """
    Login to WhatsApp Web using the BrowseWhatsApp class.
    
    This function creates a browser session with WhatsApp Web, using saved
    credentials if available. If not logged in previously, it may require
    scanning a QR code.
    
    Returns:
        A configured and logged-in BrowseWhatsApp instance.
    """
    visible = True
    userDataDir = os.path.join(BROWSER_USER_DATA_DIR, 'chromium-browser-whatsapp')
    phoneNumber = DEFAULT_ACCOUNT.noPrefix().phoneNumber
    browser = BrowseWhatsApp(visible, BROWSER_DIR, userDataDir, phoneNumber)
    browser.goTo()
    
    if not browser.isLoggedIn:
        user, message = new_email_to_self(account=DEFAULT_ACCOUNT, subject='New WhatsApp Login Required')
        message.body.paragraph('Please check the Automation Browser and login to WhatsApp via the QR code.')
        send_email_to_self(user, message) 
    
        while not browser.isLoggedIn:
            browser.wait(20)
   
    return browser


def send_whatsapp_message(
        whatsapp: BrowseWhatsApp | None = None, 
        author: str | None = None, 
        recipientContact: str | None = None, 
        recipientName: str | None = None,
        content: str | list[str] | None = None,
        targetLang: str = None) -> BrowseWhatsApp:
    """
    Send a WhatsApp message to a recipient.
    
    Args:
        whatsapp: An existing BrowseWhatsApp instance. If None, a new instance will be created.
        author: The name of the sender. Defaults to the DEFAULT_ACCOUNT name if None.
        recipientContact: The phone number of the recipient. Defaults to DEFAULT_ACCOUNT 
            phone number if None.
        recipientName: The display name of the recipient. Used for logging purposes.
        content: The message content to send. Can be a string or list of strings.
            If None, an empty list will be used.
    
    Returns:
        The BrowseWhatsApp instance used to send the message.
    """
    if not whatsapp:
        whatsapp = login_to_whatsapp()
    if not author:
        author = DEFAULT_ACCOUNT.name
    if not recipientContact:
        recipientContact = DEFAULT_ACCOUNT.reset().phoneNumber
    if not recipientName:
        recipientName = DEFAULT_ACCOUNT.name
    if not content:
        content = []
    else:
        if targetLang != 'EN-GB':
            from default.translator.functions import translate_text
            if isinstance(content, list):
                content = '\n'.join(content)
            content = translate_text(content, targetLang)
            content = content.split('\n')
    return whatsapp.sendMessage(recipientContact, content, recipientName)


def send_whatsapp_test_message(content):
    """
    Send a test WhatsApp message to the default account.
    
    Args:
        content: The message content to send. Can be a string or list of strings.
    """
    return send_whatsapp_message(content=content, recipientName='(You)')