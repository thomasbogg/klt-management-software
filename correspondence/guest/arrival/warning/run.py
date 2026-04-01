from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.arrival.functions import (
    get_guest_arrival_email_bookings,
    new_guest_arrival_email
)
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.update.wrapper import update
from utils import logerror


@update
def send_guest_warning_email(bookingId: int = None) -> str:
    """
    Send warning emails to guests about noise disturbances.
    
    Creates and sends emails to guests who have received complaints
    about noise or disturbances from condominium management.
    
    Args:
        bookingId: Optional specific booking ID to process
        
    Returns:
        str: Status message indicating success or error
    """
    database = get_database()
    bookings = get_guest_warning_bookings(database, bookingId=bookingId)
    
    if not bookings: 
        database.close()
        return logerror('GOT NO emails to send. Maybe check ID.')
    
    for booking in bookings:
        send_new_guest_warning_email(booking, bookingId)
    
    database.close()
    return 'Email sent!'


def get_guest_warning_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    bookingId: int = None
) -> list[Booking]:
    """
    Retrieve bookings for guest warning emails.
    
    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        bookingId: The specific booking ID to filter by
        
    Returns:
        list[Booking]: Booking objects that match the criteria
    """
    search = get_guest_arrival_email_bookings(
        database, start=start, end=end, bookingId=bookingId
    )
    
    # Select property address location
    select = search.propertyAddresses.select()
    select.location()
    
    return search.fetchall()


def send_new_guest_warning_email(
    booking: Booking,
    bookingId: int = None
) -> None:
    """
    Create and send warning email to guests about noise disturbances.
    
    Prepares an email explaining the complaint received from condominium management
    and reminding guests about quiet hours and respect for the property.
    
    Args:
        booking: The booking object containing guest information
        bookingId: Optional booking ID for tracking purposes
        
    Returns:
        None
    """
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(
        topic='Peace Disturbance Warning', 
        booking=booking
    )
    body: GoogleMailMessage.Body = message.body
    
    _opening(body, booking)
    _understanding(body)
    _heed_advice(body)
    _advice(body, booking)
    _cooperation(body)
    
    send_guest_email(user, message, bookingId)
    return None


# Email content sections
def _opening(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add opening paragraph explaining the complaint received.
    
    Args:
        body: The email body object to modify
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        'Unfortunately, we have received notice from the condominium management at',
        f'{booking.property.address.location} that your group was disturbing the',
        'peace last night. I must express how important it is that noise is kept',
        'to a minimum between 22:00 and 08:00.'
    )
    

def _understanding(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph acknowledging the holiday atmosphere.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We understand that Albufeira is a wonderful holiday destination, and',
        'people who visit are always keen and ready to enjoy themselves in the',
        'sun and the vibrant atmosphere on offer. This is as it should be.'
    ) 


def _heed_advice(body: GoogleMailMessage.Body) -> None:
    """
    Add transitional sentence before advice.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'But please heed this advice:'
    )


def _advice(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add detailed explanation about property expectations.
    
    Args:
        body: The email body object to modify
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        f'{booking.property.address.location} is a very prestigious property',
        'and accommodates both tourists and full-time residents. It is a place',
        'of respect that must be esteemed appropriately. We expect all our',
        'guests to treat the property as if in their own home and leave the',
        'accommodation as tidy as they found it.'
    )


def _cooperation(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph thanking for cooperation.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We appreciate your cooperation on this matter. Thank you again for',
        'choosing to stay with us.'
    )