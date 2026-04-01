from apis.google.mail.message import GoogleMailMessage
from correspondence.internal.functions import (
    get_booking_table_data, 
    new_internal_email
)
from correspondence.internal.management.functions import (
    determine_lack_of_inbound_flight_information, 
    determine_lack_of_outbound_flight_information,
    get_email_bookings
)
from correspondence.self.functions import new_bookings_email_to_self
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.google.mail.functions import send_email
from default.database.functions import (
    get_database,
    set_valid_management_booking
)
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_airport_transfers_request_emails(start: date = None, 
                                         end: date = None, 
                                         emailSent: bool = False, 
                                         bookingId: int = None) -> str:
    """
    Send email requests for airport transfers based on bookings within date range.
    
    Args:
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Filter by whether email has already been sent
        bookingId: Specific booking ID to send request for
        
    Returns:
        Status message indicating success or no emails to send
    """
    if start is None and end is None: 
        start, end = updatedates.airport_transfers_request_emails_dates()
    
    database = get_database()
    bookings = get_airport_transfers_bookings(database, start, end, emailSent, bookingId)
    
    if not bookings: 
        database.close()
        return 'NO new airport transfers emails to send.'
    
    noFlightInfo = list()
    for booking in bookings:
        if lacks_flight_information(booking):
            noFlightInfo.append(booking)
            continue
        
        send_new_airport_transfers_request_email(booking)
        
        # Update email status
        booking.emails.airportTransfers = True
        booking.update()
    
    if noFlightInfo:
        new_bookings_email_to_self(
            subject='No Flight Information for Airport Transfers Requests', 
            bookings=noFlightInfo)
    
    database.close()
    return 'All airport transfers emails sent!'


def get_airport_transfers_bookings(database: Database, 
                                  start: date = None, 
                                  end: date = None, 
                                  emailSent: bool = False, 
                                  bookingId: int = None) -> list[Booking]:
    """
    Retrieves bookings with airport transfers information.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether airport transfers email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_email_bookings(database, bookingId=bookingId, noBlocks=True)
    
    # Select details from the bookings table
    select = search.details.select()
    select.enquirySource()
    select.platformId()
    select.adults()
    select.children()
    select.babies()
    
    # Select arrival and departure details
    select = search.arrivals.select()
    select.date()
    select.time()
    select.flightNumber()
    select.isFaro()
    
    select = search.departures.select()
    select.date()
    select.time()
    select.flightNumber()
    select.isFaro()
    
    # Select extras
    select = search.extras.select()
    select.airportTransfers()
    select.airportTransferInboundOnly()
    select.airportTransferOutboundOnly()
    select.childSeats()
    select.excessBaggage()
    
    # Select guest details
    select = search.guests.select()
    select.phone()
    select.email()
    
    # Apply booking conditions
    set_valid_management_booking(search)
    
    if bookingId:
        where = search.details.where()
        where.id().isEqualTo(bookingId)
    else:
        # Apply date range conditions
        where = search.arrivals.where()
        where.date().isGreaterThanOrEqualTo(start)
        where.date().isLessThanOrEqualTo(end)
        
        # Apply email conditions
        where = search.emails.where()
        where.airportTransfers().isEqualTo(emailSent)
    
    # Apply extras conditions with OR joiner
    where = search.extras.where()
    where.airportTransfers().isTrue()
    where.joiner = 'or'
    where.airportTransferInboundOnly().isTrue()
    where.airportTransferOutboundOnly().isTrue()
    
    return search.fetchall()


#######################################################
# EMAIL FUNCTIONS
#######################################################

def lacks_flight_information(booking: Booking) -> bool:
    """
    Check if the booking lacks required flight information for transfers.
    
    Args:
        booking: The booking to check for flight information
        
    Returns:
        True if required flight information is missing, False otherwise
    """
    inboundInfo = determine_lack_of_inbound_flight_information(booking)
    outboundInfo = determine_lack_of_outbound_flight_information(booking)
    
    if booking.extras.airportTransferInboundOnly:
        return inboundInfo
    if booking.extras.airportTransferOutboundOnly:
        return outboundInfo
    return inboundInfo or outboundInfo


def send_new_airport_transfers_request_email(booking: Booking) -> None:
    """
    Create and send an airport transfer request email for a booking.
    
    Args:
        booking: The booking containing guest and transfer information
        
    Returns:
        None
    """
    subject, opening = get_subject_and_opening(booking)    
    subject += f' for {booking.guest.fullName} - {booking.property.name}'
    user, message = new_internal_email(
        to='roadrunnertransfers@gmail.com', 
        name='Wendy & Nick', 
        subject=subject
    )
    body: GoogleMailMessage.Body = message.body
    
    body.paragraph(f'I am writing to request {opening}')
    body.paragraph('Please see full details:')
    body.table(get_booking_table_data(booking, **get_kwargs_for_table(booking.extras)))
    body.paragraph('Thank you in advance. I await your confirmation.')
    
    send_email(user, message, True)


def get_kwargs_for_table(extras: Booking.extras) -> dict[str, bool]:
    """
    Returns keyword arguments for configuring booking table data display.
    
    Args:
        extras: The extras information from the booking
        
    Returns:
        Dictionary of options for table display settings
    """
    return {
        'arrivalInfo': extras.airportTransfers or extras.airportTransferInboundOnly,
        'departureInfo': extras.airportTransfers or extras.airportTransferOutboundOnly,
        'guestContactInfo': True,
        'airportTransferInfo': True,
    } 


def get_subject_and_opening(booking: Booking) -> tuple[str, str]:
    """
    Generate appropriate subject line and opening text based on transfer type.
    
    Args:
        booking: The booking containing transfer information
        
    Returns:
        Tuple containing (subject, opening text) for the email
    """
    if booking.extras.airportTransfers: 
        subject = f'Airport Transfers Request'
        opening = 'Inbound and Outbound Airport Transfers.'
        return subject, opening
    
    if booking.extras.airportTransferInboundOnly:
        subject = f'Inbound Airport Transfer Request'
        opening = 'an <b>Inbound Airport Transfer Only</b>.'
        return subject, opening
    
    subject = f'Outbound Airport Transfer Request'
    opening = 'an <b>Outbound Airport Transfer Only</b>.'
    return subject, opening