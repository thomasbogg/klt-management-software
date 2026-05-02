from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import (
    determine_balance_payment, 
    determine_balance_payment_date
)
from correspondence.guest.arrival.balance_payment.functions import get_balance_payment_bookings
from correspondence.guest.arrival.balance_payment.reminder.run import explanation
from correspondence.guest.arrival.functions import new_guest_arrival_email
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.update.wrapper import update
from PIMS.browser import BrowsePIMS
from web.browser import Browser


@update
def send_balance_payment_information_email(bookingId: int) -> str:
    """
    Send balance payment information emails to guests.
    
    Retrieves booking information, calculates the balance payment amount,
    and sends a detailed email to the guest with payment instructions.
    
    Args:
        bookingId: The ID of the specific booking to process.
        
    Returns:
        A message indicating successful email sending.
    """
    database: Database = get_database()
    bookings: list[Booking] = get_balance_payment_bookings(database, bookingId=bookingId)
    
    browser: Browser = BrowsePIMS().goTo().login()
    orderForms = browser.orderForms
    
    for booking in bookings:
        amountDue = determine_balance_payment(booking, orderForms, bookingId)
        _send_new_balance_payment_information_email(booking, amountDue, bookingId)
    
    browser.quit()
    database.close()
    return 'Emails sent!'


def _send_new_balance_payment_information_email(
    booking: Booking, 
    amountDue: str, 
    bookingId: int = None
) -> GoogleMailMessage:
    """
    Prepare and send a balance payment information email to a guest.
    
    Creates an email with details about the balance payment amount,
    due date, and payment instructions.
    
    Args:
        booking: The booking object containing guest information.
        amountDue: The formatted amount due for balance payment.
        bookingId: Optional booking ID for tracking purposes.
        
    Returns:
        The sent email message object.
    """
    topic = 'Balance Payment for Holiday'
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(topic=topic, booking=booking)
    body: GoogleMailMessage.Body = message.body
    
    _opening(body)
    _introduction(body, booking, amountDue)
    _follow_link(body)
    _link(body, booking)
    explanation(body)  # Imported from balance_payment/reminder/run.py
    _conclusion(body)    
    
    send_guest_email(user, message, bookingId)
    return message


def _opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Thank you very much for consulting with me about the balance payment for',
        'your holiday.'
    )


def _introduction(
    body: GoogleMailMessage.Body, 
    booking: Booking, 
    amountDue: str
) -> None:
    """
    Add the introduction paragraph with balance payment details.
    
    Includes the amount due and the payment deadline calculated based on
    the arrival date.
    
    Args:
        body: The email body object to modify.
        booking: The booking object with arrival information.
        amountDue: The formatted amount due for balance payment.
        
    Returns:
        None
    """
    dueDate = determine_balance_payment_date(booking)
    body.paragraph(
        f'The outstanding <b>Holiday Rental Balance of {amountDue}</b> is',
        'officially due 8 weeks prior to the arrival date. This means that the',
        f'payment should be made by <b>{dueDate}</b>. I will be contacting you',
        'nearer the time with a reminder, so you don\'t have to do anything for',
        'now.'
    )


def _follow_link(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph about early payment option.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'If, however, you wish to make the payment earlier, you may follow the',
        'link below at your convenience.'
    )


def _link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add the balance payment link paragraph.
    
    Args:
        body: The email body object to modify.
        booking: The booking object containing the balance payment form link.
        
    Returns:
        None
    """
    body.link(
        booking.forms.balancePayment, 
        'Balance Payment Form Link'
    )


def _conclusion(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(   
        'I hope this has been informative and helpful. As always, I remain',
        'available.'
    )