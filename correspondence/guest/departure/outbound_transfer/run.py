from apis.google.mail.message import GoogleMailMessage
from correspondence.guest.departure.functions import (
    get_guest_departure_email_bookings,
    new_guest_departure_email
)
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.booking.functions import determine_price_of_extra
from default.database.database import Database
from default.database.functions import get_database
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_outbound_transfer_confirmation_email(bookingId: int = None) -> str:
    """
    Send confirmation email for outbound airport transfer.
    
    Args:
        bookingId: The ID of the booking to send confirmation for
        
    Returns:
        Status message indicating success or failure
    """
    if bookingId is None: 
        return 'ERROR: No Booking ID specified!'
    
    database = get_database()
    booking = get_outbound_transfer_booking(database, bookingId=bookingId)
    
    if not booking: 
        database.close()
        return 'FOUND no booking to send email.'
    
    new_outbound_transfer_confirmation_email(booking, bookingId)
    
    database.close()
    return 'Email sent!'


def get_outbound_transfer_booking(database: Database, bookingId: int = None) -> Booking | None:
    """
    Retrieves outbound transfer booking information for a specific booking.

    Args:
        database: The database connection object
        bookingId: The specific booking ID to retrieve

    Returns:
        The first booking that matches the criteria or None if no match found
    """
    # Initialize search using the higher-level function
    search = get_guest_departure_email_bookings(database, bookingId=bookingId)
    
    # Select departure date
    select = search.departures.select()
    select.flightNumber()  # Replaces outbound_number
    select.time()          # Replaces outbound_time
    select.isFaro()        # Replaces is_Faro_take_off
    
    # Select stay information for passenger counts
    select = search.details.select()
    select.adults()
    select.children()
    select.babies()
    
    return search.fetchone()


def new_outbound_transfer_confirmation_email(booking: Booking, bookingId: int) -> None:
    """
    Create and send an outbound transfer confirmation email to the guest.
    
    Args:
        booking: The booking containing guest and property information
        bookingId: The ID of the booking
        
    Returns:
        None
    """
    user, message = new_guest_departure_email(topic='Outbound Transfer Confirmation for', booking=booking)
    body = message.body
    
    opening(body, booking)
    time(body, booking)
    check_details(body)
    contact(body)
    cost(body, booking)
    conclusion(body)
    
    send_guest_email(user, message, bookingId)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def opening(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with departure information
        
    Returns:
        None
    """
    body.paragraph(
        'Your airport transfer to Faro airport has been booked for',
        f'<b>{booking.departure.date}</b>.',
    )


def time(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add flight time and pick-up information to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with flight information
        
    Returns:
        None
    """
    flightNumber = booking.departure.flightNumber
    flightTime = booking.departure.time
    body.paragraph(
        'The driver will be waiting for you outside the main entrance of the',
        'building <b>2h45m</b> before your scheduled take-off time of',
        f'<b>{flightTime}</b> on flight <b>{flightNumber}</b>.'
    )


def check_details(body: GoogleMailMessage.Body) -> None:
    """
    Add request to verify details to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'If any of the previous details are incorrect, please let me know as',
        'soon as possible. Thank you.'
    )


def contact(body: GoogleMailMessage.Body) -> None:
    """
    Add contact information for the transfer company to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'In the exceptional event that the driver is not on time or should you',
        'need to make alternative pick-up arrangements, you may contact the',
        'transfer company directly on +351 919 269 411.'
    )


def cost(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add cost information for the transfer to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with cost information
        
    Returns:
        None
    """
    price = determine_price_of_extra(booking, 'airport transfer outbound')
    body.paragraph(
        f'The cost of this airport transfer is <b>{price}</b> and should be paid',
        'directly to the driver in cash.'
    )


def conclusion(body: GoogleMailMessage.Body) -> None:
    """
    Add conclusion to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this is clear. As always, I remain available for questions.',
    )