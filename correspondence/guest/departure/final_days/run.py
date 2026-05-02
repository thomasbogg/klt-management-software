from apis.google.mail.message import GoogleMailMessage
from correspondence.functions import determine_outbound_transfer
from correspondence.guest.departure.functions import (
    get_guest_departure_email_bookings,
    new_guest_departure_email
)
from correspondence.guest.functions import send_guest_email
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.mail.functions import valid_email_address
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_final_day_reminder_emails(start: date = None, 
                                  end: date = None, 
                                  emailSent: bool = False, 
                                  bookingId: int = None) -> str:
    """
    Send reminder emails to guests about their final day procedures.
    
    Args:
        start: Starting date for departure range
        end: Ending date for departure range
        emailSent: Filter by whether email has already been sent
        bookingId: Specific booking ID to send reminder for
        
    Returns:
        Status message indicating success or no emails to send
    """
    if not bookingId and start is None and end is None: 
        start, end = updatedates.final_day_reminder_emails_dates()

    database = get_database()
    bookings = get_final_days_reminder_bookings(database, start, end, emailSent, bookingId)
    
    if not bookings:
        database.close()
        return 'NO new emails to send.'

    for booking in bookings:
        guestEmail = booking.guest.email
        if valid_email_address(address=guestEmail):
            if guestEmail not in booking.property.owner.email:
                new_final_day_reminder_email(booking, bookingId)            
        
        # Update email status
        booking.emails.finalDaysReminder = True
        booking.update()

    database.close()
    return 'All emails sent!'


def get_final_days_reminder_bookings(database: Database, 
                                    start: date = None, 
                                    end: date = None, 
                                    emailSent: bool = False, 
                                    bookingId: int = None) -> list[Booking]:
    """
    Retrieves bookings for final days reminder emails with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering departures
        end: The end date for filtering departures
        emailSent: Whether final days reminder email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_guest_departure_email_bookings(database, start=start, end=end, 
                                                bookingId=bookingId)
    
    # Select extras details
    select = search.extras.select()
    select.airportTransfers()
    select.airportTransferOutboundOnly()
    select.lateCheckout()
    
    # Select property address details
    select = search.propertyAddresses.select()
    select.nearestBins()
    
    # Apply email conditions if not filtering by bookingId
    if not bookingId:
        where = search.emails.where()
        where.finalDaysReminder().isEqualTo(emailSent)
    
    return search.fetchall()


def new_final_day_reminder_email(booking: Booking, bookingId: int) -> None:
    """
    Create and send a final day reminder email to a guest.
    
    Args:
        booking: The booking containing guest and property information
        bookingId: The ID of the booking
        
    Returns:
        None
    """
    user, message = new_guest_departure_email(topic='Final Days Reminder for', booking=booking)
    body = message.body

    opening(body)
    introduction(body)
    
    if booking.extras.lateCheckout:
        late_checkout(body, booking)
    else:
        normal_checkout(body, booking)
    
    if booking.property.isQuintaDaBarracuda: 
        means_of_exit(body)
    elif determine_outbound_transfer(booking):
        airport_transfer(body)
    
    wash_up(body)
    clean_appliances(body)
    if booking.property.shortName == 'MON T':
        clean_bbq(body)
    
    bins = booking.property.address.nearestBins
    if bins:
        empty_rubbish(body, booking)
    
    empty_fridge(body)
    if (
        booking.property.isQuintaDaBarracuda or
        booking.property.isClubeDoMonaco
    ):
        complex_access(body)
    
    appreciation(body)
    closing(body)

    send_guest_email(user, message, bookingId)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening greeting to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I hope you have been having a lovely time in Albufeira!',
    )


def introduction(body: GoogleMailMessage.Body) -> None:
    """
    Add introduction about the final day procedure.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'As your stay with us is coming to its end I would like to take a moment',
        'to speak about the final day procedure.',
    )


def normal_checkout(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add standard checkout instructions to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with departure information
        
    Returns:
        None
    """
    body.paragraph(
        f'<u>Check-out is at 10.00am on {booking.departure.prettyDate} unless a',
        'different time has previously been agreed</u>. When departing, simply',
        'leave all keys and fobs on the dining table and close the door behind you.'
    )


def late_checkout(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add late checkout instructions to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking with departure information
        
    Returns:
        None
    """
    body.paragraph(
        f'<u>Check-out would normally be at 10.00am on {booking.departure.prettyDate},',
        'but you have requested a late departure</u>. So, please enjoy the',
        'apartment for as long as needed on your last day. When ready to leave',
        'for the final time, simply put the keys on the dining table and close',
        'the door behind you.'
    )


def means_of_exit(body: GoogleMailMessage.Body) -> None:
    """
    Add information about exiting the Quinta da Barracuda property.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'If you have booked our airport transfers, the driver will be waiting for',
        'you in the front courtyard at the main entrance <u>2h45m before your',
        'scheduled take-off time</u> - unless a different time was previously',
        'discussed. Alternatively, if you are driving out, the gate will open',
        'automatically as you approach it in the vehicle. Or if you have arranged',
        'other means, such as Uber or local or private taxi services, you can use',
        'the release button on the pedestrian side gate to reach the transport on',
        'the main road.',
    )


def airport_transfer(body: GoogleMailMessage.Body) -> None:
    """
    Add information about booked airport transfers.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'As you have booked our airport transfer, the driver will be waiting for',
        'you outside the main entrance <u>2h45m before your scheduled take-off',
        'time</u> - unless a different time was previously discussed.'
    )


def wash_up(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions about washing dishes before departure.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I would respectfully ask you to ensure that all used crockery and',
        'cutlery has been cleaned and stored away.'
    )


def clean_appliances(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions about cleaning kitchen appliances.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'It is also requested that kitchen appliances, particularly the oven and',
        'microwave, are left as clean as you found them.'
    )


def clean_bbq(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions about cleaning the BBQ before departure.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'If you have used the BBQ, please ensure it is cleaned and left in a',
        'satisfactory condition. Failure to do so may result in a charge of €50.00.',
    )


def empty_rubbish(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add instructions about disposing of trash before departure.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        'Please also remember to take the rubbish to the containers which are',
        f'situated {booking.property.address.nearestBins}. (You can find',
        'instructions about this behind the door.)',
    )


def empty_fridge(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions about emptying the refrigerator.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'And kindly endeavour to refrain from leaving food in tupperware and',
        'opened bottles of soft drink in the fridge.'
    )


def complex_access(body: GoogleMailMessage.Body) -> None:
    """
    Add information about accessing complex facilities after checkout.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        '<u>General access to the building complex and facilities, such as pool',
        'area, luggage storage and the communal showers after check-out is',
        'available</u>. Should it be required, kindly reply to this email, and I',
        'will forward instructions on how to proceed.'
    )


def appreciation(body: GoogleMailMessage.Body) -> None:
    """
    Add a message of appreciation.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'We sincerely appreciate your cooperation on these matters. Thank you.'
    )


def closing(body: GoogleMailMessage.Body) -> None:
    """
    Add closing message to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'Enjoy your last moments, and we wish you a safe journey home!'
    )