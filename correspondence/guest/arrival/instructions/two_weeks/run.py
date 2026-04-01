from datetime import date

from correspondence.guest.arrival.instructions.functions import (
    determine_inbound_transfer,
    get_arrival_instructions_bookings,
    get_changeover_bookings,
    send_new_arrival_instructions_email,
)
from correspondence.guest.arrival.instructions.two_weeks.missing_details.run import (
    send_new_missing_arrival_information_email
)
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.mail.functions import valid_email_address
from default.update.dates import updatedates
from default.update.wrapper import update


@update
def send_two_weeks_instructions_emails(
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> str:
    """
    Send arrival information emails to guests arriving in two weeks.
    
    Args:
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        emailSent: Whether to filter for bookings that already received emails
        bookingId: Optional specific booking ID to process
        
    Returns:
        str: Status message indicating success or no emails to send
    """
    if not bookingId and start is None and end is None: 
        start, end = updatedates().arrival_information_emails_dates()
    
    database = get_database()
    bookings = get_two_weeks_arrival_bookings(
        database, start, end, emailSent, bookingId
    )
    
    if not bookings: 
        database.close()
        return 'NO new emails to send.'
    
    for booking in bookings:
        
        if should_send_email(booking):
            if not booking.guest.email or not valid_email_address(booking):
                if not booking.details.isOwner:
                    continue
                if not determine_inbound_transfer(booking):
                    continue

            # Check if direct booking has already had security deposit request email sent
            if (
                not bookingId and 
                not booking.details.isOwner and 
                not booking.details.isPlatform and 
                not booking.emails.securityDepositRequest): 
                continue

            if not booking.arrival.hasDetails:
                if booking.property.shortName == 'B11': 
                    continue
                if booking.details.isPlatform: 
                    continue
                if not booking.forms.arrivalQuestionnaire:
                    send_new_missing_arrival_information_email(booking)
                continue

            # Check for changeover
            changeoverBookings = get_changeover_bookings(
                database, booking.arrival.date, booking.guest.id
            )
            if not changeoverBookings and not booking.emails.checkInInstructions:
                send_new_arrival_instructions_email(
                    topic='Arrival Information',
                    booking=booking,
                    bookingId=bookingId,
                    twoWeeks=True
                )

        # Update email status
        booking.emails.arrivalInformation = True
        booking.update()

    database.close()
    return 'All emails sent!'


def get_two_weeks_arrival_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> list[Booking]:
    """
    Get bookings that need two-week arrival information emails.
    
    Args:
        database: Database connection
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        emailSent: Whether to filter for bookings that already received emails
        bookingId: Optional specific booking ID to retrieve
        
    Returns:
        list[Booking]: Bookings that need arrival information emails
    """
    search = get_arrival_instructions_bookings(
        database, start=start, end=end, bookingId=bookingId
    )
   
    select = search.emails.select()
    select.checkInInstructions()
   
    if bookingId is None:
        where = search.emails.where()
        where.arrivalInformation().isEqualTo(emailSent)
   
    return search.fetchall()


def should_send_email(booking: Booking) -> bool:
    """
    Determine if an arrival information email should be sent to a guest.
    
    Args:
        booking: The booking to check
        
    Returns:
        bool: True if an email should be sent, False otherwise
    """
    # Always send for meet & greet bookings
    if booking.arrival.meetGreet:
        return True
   
    # Owner booking checks
    if booking.details.isOwner:
        # Don't send if guest name contains 'owner'
        if 'owner' in booking.guest.prettyName.lower():
            return False
        
        if not booking.arrival.hasDetails and booking.forms.arrivalQuestionnaire:
            return True
    
        # Send if booking includes airport transfers
        if booking.extras.airportTransfers:
            return True
        
        if booking.extras.airportTransferInboundOnly:
            return True
    
    return False