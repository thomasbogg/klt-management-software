from correspondence.internal.accountancy.functions import (
    get_accountancy_email_bookings,
    new_accountancy_email
)
from datetime import date
from default.booking.booking import Booking
from default.booking.functions import determine_security_deposit_request
from default.database.database import Database
from default.database.functions import get_database
from default.google.mail.functions import send_email
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_security_deposit_returns_email(
        start: date = None, 
        end: date = None, 
        daily: bool = True, 
        emailSent: bool = False, 
        bookingId: int = None) -> str:
    """
    Send email notification about security deposits that need to be returned.
    
    Args:
        start: The start date for filtering departures
        end: The end date for filtering departures
        daily: Whether this is a daily update email
        emailSent: Filter by whether email has already been sent
        bookingId: Specific booking ID to include
        
    Returns:
        Status message indicating success or no deposits to return
    """
    if start is None and end is None: 
        start, end = updatedates.security_deposit_returns_email_dates()
    
    database = get_database()
    bookings = get_security_deposit_returns_bookings(database, start, end, emailSent, bookingId)
    
    filteredBookings = []
    for booking in bookings:
        if determine_security_deposit_request(booking): 
            filteredBookings.append(booking)
    
    if not filteredBookings: 
        database.close()
        return f'NO SECURITY DEPOSIT RETURNS for period {start} TO {end}.'
    
    new_security_deposit_returns_email(filteredBookings, start, end, daily)
    
    for booking in filteredBookings: 
        booking.emails.securityDepositReturn = True
        booking.update()
    
    database.close()
    return 'Email sent!'


def get_security_deposit_returns_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves security deposit returns bookings with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering departures
        end: The end date for filtering departures
        emailSent: Whether security deposit return email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_accountancy_email_bookings(database, bookingId=bookingId)

    # Select general details
    select = search.details.select()
    select.isOwner()
    
    # Select departure date
    select = search.departures.select()
    select.date()
    
    # Select charges details
    select = search.charges.select()
    select.currency()
    select.security()
    select.securityMethod()
    
    # Select forms details
    select = search.forms.select()
    select.securityDeposit()
    select.PIMSuin()
    select.PIMSoid()
    
    # Select guest details
    select = search.guests.select()
    select.id()
    select.email()
    
    # Apply conditions
    if bookingId is None:
        # Apply date range conditions if provided
        where = search.departures.where()
        where.date().isGreaterThanOrEqualTo(start)
        where.date().isLessThanOrEqualTo(end)
        
        # Apply booking conditions
        where = search.details.where()
        where.enquirySource().isEqualTo("Direct")  # direct_booking=True
        
        # Apply charges conditions
        where = search.charges.where()
        where.security().isNotNullEmptyOrFalse()  # has_security=True
        
        # Apply email conditions
        where = search.emails.where()
        where.securityDepositReturn().isEqualTo(emailSent)
    
    return search.fetchall()


#######################################################
# EMAIL CREATION FUNCTIONS
#######################################################

def new_security_deposit_returns_email(
        bookings: list[Booking], 
        start: date, 
        end: date, 
        daily: bool) -> None:
    """
    Create and send an email about security deposits that need to be returned.
    
    Args:
        bookings: List of bookings with security deposits to return
        start: The start date for the email date range
        end: The end date for the email date range
        daily: Whether this is a daily update email
        
    Returns:
        None
    """
    user, message = new_accountancy_email(
        topic='SECURITY DEPOSIT RETURNS', 
        start=start, 
        end=end, 
        daily=daily
    )
    body = message.body
    body.paragraph(f'There are {len(bookings)} security deposits to return:', underlined=True)
    count = 1
    
    for booking in bookings:
        guestLine = (
            f'<b>{count})</b> {booking.guest.fullName}',
            f'in {booking.property.shortName}',
            f'arrived {booking.arrival.prettyDate}',
            f'departed {booking.departure.prettyDate}',
        )
        body.paragraph(*guestLine)
        
        method = booking.charges.securityMethod
        if method != 'Cash': 
            body.paragraph(f'Note: did not pay in cash but {method}')
            
        body.paragraph(f'Email: {booking.guest.email}')
        body.paragraph('Bank details here:')
        body.paragraph(booking.forms.securityDeposit)
        count += 1
        
    send_email(user, message)