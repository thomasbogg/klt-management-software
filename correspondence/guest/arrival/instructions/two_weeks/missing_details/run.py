from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.arrival.functions import new_guest_arrival_email
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking


def send_new_missing_arrival_information_email(
    booking: Booking,
    bookingId: int = None
) -> None:
    """
    Send an email to guests who haven't provided arrival information.
    
    Creates and sends an email to guests requesting missing arrival details such as
    flight information and estimated arrival time.
    
    Args:
        booking: The booking object containing guest information
        bookingId: Optional booking ID for tracking purposes
        
    Returns:
        None
    """
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(topic='Missing Arrival Details', booking=booking)
    body: GoogleMailMessage.Body = message.body
    
    _opening(body)
    _explainer(body, booking)
    _missing_flights(body)
    _other_details(body)
    _closing(body)
    
    send_guest_email(user, message, bookingId)
    return None


def _opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We are only two weeks away from the start of your holiday. You must be',
        'looking forward to it!'
    )


def _explainer(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add explanation paragraph about sending arrival instructions.
    
    Args:
        body: The email body object to modify
        booking: The booking with arrival date information
        
    Returns:
        None
    """
    body.paragraph(
        'This is now the time for me to send the Arrival Instructions which will',
        'give you the required information about the location of the apartment',
        'and how to get access to it on', 
        f'{booking.arrival.prettyDate}.'
    )


def _missing_flights(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph requesting flight information.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'However, before I can do this, we need to know your inbound flight',
        'number and its scheduled landing time, as well as your outbound flight',
        'number and its scheduled take-off time.'
    )


def _other_details(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph requesting alternative transport details if not flying.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'If you are not flying in to Faro on the day of your holiday start,',
        'could you please let us know what mode of transport you are planning',
        'to use and give us an Estimate Time of Arrival at the property?'
    )


def _closing(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We really appreciate this extra information as it helps us keep on top',
        'of our preparation for your time with us.'
    )