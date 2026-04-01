from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.arrival.functions import (
    code_of_conduct_explainer,
    get_guest_arrival_email_bookings,
    get_code_of_conduct_attachment,
    linen_care_1,
    linen_care_2,
    new_guest_arrival_email
)
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.booking.functions import determine_security_deposit_request
from default.database.database import Database
from default.database.functions import get_database
from default.update.dates import updatedates
from default.update.wrapper import update


@update
def send_security_deposit_request_emails(
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> str:
    """
    Send security deposit request emails to guests within a date range.
    
    Args:
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        emailSent: Whether to filter for bookings that already received emails
        bookingId: Optional specific booking ID to process
        
    Returns:
        str: Status message indicating success or no emails to send
    """
    if not bookingId and start is None and end is None: 
        start, end = updatedates.security_deposit_request_emails_dates()

    database = get_database()
    bookings = get_security_deposit_request_bookings(
        database, start, end, emailSent, bookingId
    )
    
    if not bookings: 
        database.close()
        return 'NO new emails to send.'
    
    for booking in bookings:
        if determine_security_deposit_email(booking):
            send_new_security_deposit_request_email(booking, bookingId)        
        
        # Update email status
        booking.emails.securityDepositRequest = True
        booking.update()
    
    database.close()
    return 'All emails sent!'


def determine_security_deposit_email(
    booking: Booking
) -> bool:
    if booking.details.isOwner:
        return False
    if booking.details.isPlatform:
        return False
    return True


def get_security_deposit_request_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> list[Booking]:
    """
    Retrieve bookings for security deposit requests with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether security deposit request email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        list[Booking]: Booking objects that match the criteria
    """
    # Initialize the search using the higher-level function
    search = get_guest_arrival_email_bookings(
        database, start=start, end=end, bookingId=bookingId
    )
    
    # Add charges selections
    select = search.charges.select()
    select.currency()
    select.security()
    select.securityMethod()
    
    # Add forms selections
    select = search.forms.select()
    select.securityDeposit()
    select.PIMSuin()
    select.PIMSoid()
    
    # Apply conditions
    where = search.details.where()
    where.enquirySource().isEqualTo("Direct")  # direct_booking=True
    where.isOwner().isFalse()  # owner_booking=False
    
    # Apply email conditions if not filtering by bookingId
    if not bookingId:
        where = search.emails.where()
        where.securityDepositRequest().isEqualTo(emailSent)
    
    return search.fetchall()


def send_new_security_deposit_request_email(
    booking: Booking,
    bookingId: int = None
) -> None:
    """
    Create and send a security deposit request email to a guest.
    
    Prepares an email explaining security deposit requirements or informing
    guests if the deposit is waived.
    
    Args:
        booking: The booking object containing guest information
        bookingId: Optional booking ID for tracking purposes
        
    Returns:
        None
    """
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(topic='Security Deposit Request', booking=booking)
    body: GoogleMailMessage.Body = message.body

    _opening(body)
    _introduction(body)
    body.separation()

    # Security Deposit section
    body.section('Security Deposit')
    if determine_security_deposit_request(booking):
        _instructions(body)
        _explanation(body)
        _fill_in_form(body)
        _link(body, booking)
    else:
        _deposit_not_required(body)
    
    # Towel and Linen care section
    body.section('Towel and Linen Care')
    linen_care_1(body)
    linen_care_2(body)
    
    # Albufeira code of conduct section
    body.section('Albufeira\'s Tourist Code of Conduct')
    message.attachments = get_code_of_conduct_attachment()
    code_of_conduct_explainer(body)

    body.separation()
    _thank_you(body)
    _next_email_notice(body)
    
    send_guest_email(user, message, bookingId)
    return None


# Email content sections
def _opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'You must be counting the hours now!'
    )


def _introduction(body: GoogleMailMessage.Body) -> None:
    body.paragraph(
        'The next thing we need to do is clarify some aspects of your upcoming stay.',
        'This email contains three important topics: Security Deposit, Linen and Towel',
        'Care, and the Albufeira Tourist Code of Conduct. We kindly ask that you give',
        'all three sections below your focused attention.'
    )


def _instructions(body: GoogleMailMessage.Body) -> None:
    """
    Add security deposit payment instructions.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We need to clarify the payment of the Security Deposit. To receive the keys to the',
        'apartment, it is important that you hand over €200 in cash at check-in.'
    ) 


def _explanation(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation about security deposit refund process.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'After departure, as soon as we have confirmed that all has been left well',
        'with the property, the deposit will be refunded via Bank Transfer.',
        'Doing this part of the process electronically is preferable because it makes',
        'your exit smoother and reduces the chance of delays, especially during',
        'the busiest times of the year.'
    )


def _fill_in_form(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph requesting form completion for bank details.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Therefore, could you please provide us with the bank account information',
        'necessary for the return payment by filling in the following form:'
    )


def _link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add security deposit form link to the email.
    
    Args:
        body: The email body object to modify
        booking: The booking with form information
        
    Returns:
        None
    """
    body.link(
        booking.forms.securityDeposit, 
        'Security Deposit Details Form'
    )


def _thank_you(body: GoogleMailMessage.Body) -> None:
    """
    Add thank you paragraph to the email body.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Thank you very much in advance for your understanding and cooperation.'
    )


def _next_email_notice(body: GoogleMailMessage.Body) -> None:
    """
    Add information about upcoming joining instructions email.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Next week, I will be sending through Joining Instructions. These will provide',
        'you with all the required information in anticipation of your arrival.',
        'Not long to go!'
    )
    

def _deposit_not_required(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph for cases where security deposit is waived.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'This section would normally contain a request for a Security Deposit. However,',
        'as you are a valued guest, we are very happy to forego this formality.'
    )