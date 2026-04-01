from apis.google.mail.message import GoogleMailMessage
from correspondence.guest.departure.functions import (
    get_guest_departure_email_bookings,
    new_guest_departure_email
)
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.update.wrapper import update
from utils import logerror


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_after_check_out_email(bookingId: int | None = None) -> str:
    """
    Send an email to the guest with after check-out access information.
    
    Args:
        bookingId: The ID of the booking to send the email for
        
    Returns:
        Message indicating success or failure
    """
    if bookingId is None: 
        return logerror('No Booking ID specified!')
    
    database = get_database()
    booking = get_after_checkout_booking(database, bookingId=bookingId)
    
    if booking is None: 
        database.close()
        return 'FOUND no booking to send email.'
    
    if not booking.property.isClubeDoMonaco and not booking.property.isQuintaDaBarracuda:
        database.close()
        return logerror(f'Property {booking.property.name} does not support After Check Out emails.')
    
    new_after_check_out_email(booking, bookingId)
    
    database.close()
    return 'Email sent!'


def get_after_checkout_booking(database: Database, bookingId: int | None = None) -> Booking | None:
    """
    Retrieves a booking for after check-out functionality.

    Args:
        database: The database connection object
        bookingId: The specific booking ID to retrieve

    Returns:
        The first booking that matches the criteria or None if no match found
    """
    search = get_guest_departure_email_bookings(database, bookingId=bookingId)
    return search.fetchone()


def new_after_check_out_email(booking: Booking, bookingId: int) -> None:
    """
    Create and send an after check-out email to the guest.
    
    Args:
        booking: The booking object containing guest and property information
        bookingId: The ID of the booking
        
    Returns:
        None
    """
    user, message = new_guest_departure_email(topic='After Check-out Access for', booking=booking)
    body = message.body

    opening(body, booking)

    if booking.property.isQuintaDaBarracuda: 
        building_access(body, booking)
        luggage_storage(body, booking)
        luggage_storage_room(body)
        beach_towels(body, booking)
        bathroom_facilities(body, booking)
        deposit_fob(body)
    else:
        building_access(body, booking)
        luggage_storage(body, booking)
        bathroom_facilities(body, booking)
            
    conclusion(body)
    closing(body)

    send_guest_email(user, message, bookingId)
    return None


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
        'I understand that you would like access to the general complex and',
        'facilities after completing your check-out on',
        f'{booking.departure.prettyDate}.',
    )


def conclusion(body: GoogleMailMessage.Body) -> None:
    """
    Add conclusion paragraph to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this is clear. As always, I remain available for further questions.',
    )


def closing(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'Wish you a great last day and a safe journey onward!',
    )


def building_access(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add building access information to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
        body.paragraph(
            'To enable easy and free entry and exit from the gated area of Quinta',
            'da Barracuda, take <b>a blue fob</b> (pedestrian and beach gate magnet)',
            'from one of the sets of keys. (Note: <u>please put all door keys and',
            'other fobs on the dining room table</u> before you leave the apartment',
            'for the last time.)',
        )
    else:
        body.paragraph(
            'To get in and out of the building without keys, use the keypad on the',
            'right-hand side of the front entrance, pressing <b>9999</b> to enter.',
        )


def luggage_storage(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add luggage storage information to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
        body.paragraph(
            'If <u>luggage storage</u> is needed, you are invited to use the private',
            'room on the left-hand side of the seating area in the main lobby. If you',
            'have not noticed this area and/or room before, please read the following:',
        )
    else:
        body.paragraph(
            'You are welcome to store your cases in the space behind the stairs on',
            'the ground floor. This is the gap between the back of the stairs and',
            'the sofas just before apartment 8.',
        )


def luggage_storage_room(body: GoogleMailMessage.Body) -> None:
    """
    Add detailed luggage storage room information to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        '<i>As you stand in the centre of the lobby on floor -1 and face the',
        'stairs behind the sliding glass doors that lead up to the pool, and look',
        'to the left, you will see the seating area, and just at the other side of',
        'this space there is a door to a little room which is perfect for storing',
        'luggage for as long as is required.</i>',
    )


def bathroom_facilities(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add bathroom facilities information to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
        body.paragraph(
            'There are also communal showers in the main lobby area which can be',
            'used for bathing.',
        )
    else:
        body.paragraph(
            'The communal showers are on the same floor as the pool, located in',
            'the toilets to be found by heading straight on rather than turning',
            'right to the pool as you come off the stairs on level -1.',
        )


def beach_towels(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add beach towels information to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
        body.paragraph(
            'You are welcome to take <u>the beach towels</u> with you and make use',
            'of them for any pool or beach activities before your final departure.',
            'But if you do intend to take them, please inform me by replying to',
            'this email so that I can make a note for the cleaning staff. You may',
            'then <u>drop them off in the luggage storage room</u> when finished.',
        )
    else:
        body.paragraph(
            'Please also feel free to take the beach towels from the apartment if',
            'they will be of use. Once you are finished with them, just drop them',
            'on the table in the private room next to the vending machine on the',
            'ground floor. There is a sign on the door that says something like',
            '"Private. No entry." Don\'t worry about the sign, simply open the door',
            'and place the towels on top of the coffee table you will see just in',
            'front of a sofa.',
        )


def deposit_fob(body: GoogleMailMessage.Body) -> None:
    """
    Add fob deposit information to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'As you depart Quinta da Barracuda for the last time, kindly deposit',
        '<b>the blue fob in post-box B31</b> which you will find on the left-hand',
        'side on exiting the front gate.'
    )