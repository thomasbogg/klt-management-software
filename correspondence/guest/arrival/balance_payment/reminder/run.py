from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import determine_balance_payment
from correspondence.guest.arrival.balance_payment.functions import get_balance_payment_bookings
from correspondence.guest.arrival.functions import new_guest_arrival_email
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.update.dates import updatedates
from default.update.wrapper import update
from PIMS.browser import BrowsePIMS
from web.browser import Browser


@update
def send_balance_payment_emails(
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None
) -> str:
    """
    Send reminder emails for balance payments due within the specified date range.
    
    Identifies bookings in the given date range where balance payments are due,
    calculates the amount due, and sends reminder emails to guests.
    
    Args:
        start: The start date for filtering bookings. If None, uses default dates.
        end: The end date for filtering bookings. If None, uses default dates.
        emailSent: Whether to include bookings where reminder emails have already been sent.
        bookingId: Optional specific booking ID to process.
        
    Returns:
        A message indicating the outcome of the email sending operation.
    """
    if bookingId is None and start is None and end is None: 
        start, end = updatedates.balance_payment_emails_dates()

    database: Database = get_database()
    bookings: list[Booking] = get_balance_payment_bookings(
        database, start, end, emailSent, bookingId
    )
    
    if not bookings: 
        database.close()
        return 'No new emails to send.'

    browser: Browser = BrowsePIMS().goTo().login()
    orderForms = browser.orderForms

    for booking in bookings:
        amountDue: str = determine_balance_payment(booking, orderForms, bookingId)
        if amountDue:
            _send_new_balance_payment_email(booking, amountDue, bookingId)    
        booking.emails.balancePayment = True
        booking.emails.update()

    browser.quit()
    database.close()
    return 'Emails sent!'


def _send_new_balance_payment_email(
    booking: Booking, 
    amountDue: str, 
    bookingId: int = None
) -> GoogleMailMessage:
    """
    Prepare and send a balance payment reminder email to a guest.
    
    Creates an email with payment instructions and details about the
    outstanding balance amount.
    
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
    _introduction(body, amountDue)
    _follow_link(body)
    _link(body, booking)
    explanation(body)
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
        'I hope this finds you well.'
    )


def _introduction(body: GoogleMailMessage.Body, amountDue: str) -> None:
    """
    Add introduction paragraph with payment details to the email body.
    
    Args:
        body: The email body object to modify.
        amountDue: The formatted amount due for balance payment.
        
    Returns:
        None
    """
    body.paragraph(
        'As we are approaching the start of your holiday (not long now!), this',
        'is just a friendly reminder that <b>the Holiday Rental Balance of',
        f'{amountDue} will be due in the next 7 days</b>.'
    )


def _follow_link(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph prompting user to use the payment link.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Please follow the link below to complete the payment.'
    )


def _link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add payment link to the email body.
    
    Args:
        body: The email body object to modify.
        booking: The booking object containing the payment link.
        
    Returns:
        None
    """
    body.link(
        booking.forms.balancePayment, 
        'Balance Payment Form Link'
    )


def explanation(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation of optional extras available for booking.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'The form also contains a section on Optional Extras. Please take a',
        'moment to consider whether we might be able to provide additional',
        'services like <b>Airport Transfers</b>, <b>Welcome Pack</b>, <b>Cot',
        'and/or High Chair</b>, <b>Mid-stay Clean</b>. All these can be paid for',
        'in cash upon arrival. The welcome pack includes bread, butter, eggs,',
        'jam, milk, water, wine, beer, tea, coffee. The mid-stay clean includes',
        'a towel and linen change.'
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
        'Once we have received confirmation of payment we will contact you to',
        'let you know that all is running smoothly and we are on direct course',
        'for your holiday!'
    )