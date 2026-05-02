from correspondence.internal.functions import (
    get_booking_table_data,
    get_subject, 
    new_internal_email
)
from correspondence.internal.management.functions import (
    determine_manager_email,
    determine_manager_name,
    get_management_email_bookings
)
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database,
    set_valid_management_booking,
)
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_management_arrivals_emails(
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        weClean: bool = False, 
        bookingId: int = None) -> str:
    """
    Send email notifications to managers about upcoming property arrivals.
    
    Args:
        start: Starting date for arrival range
        end: Ending date for arrival range
        emailSent: Filter by whether email has already been sent
        weClean: Filter for properties we clean
        bookingId: Specific booking ID to send information about
        
    Returns:
        Status message indicating success or no bookings to report
    """
    general = True
    if start is None and end is None: 
        general = False
        start, end = updatedates.management_arrivals_emails_dates()
    
    database = get_database()
    bookings = get_management_arrivals_email_bookings(database, start, end, emailSent, weClean, bookingId)
    
    if not bookings: 
        database.close()
        return 'Got no bookings to send to arrivals managers!'
    
    send_new_management_arrivals_email(bookings, start, end, daily=True)
    
    # Update email status
    if not general:
        for booking in bookings:
            booking.emails.management = True
            booking.update()
    
    database.close()
    return 'All emails to managers sent!'


def get_management_arrivals_email_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        weClean: bool = False, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves management arrivals email bookings with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether management arrival email has been sent
        weClean: Whether to filter for properties we clean
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_management_email_bookings(database, start=start, end=end, emailSent=emailSent, bookingId=bookingId)
    
    # Select arrival details - meetGreet now in arrivals table, not stays table
    select = search.arrivals.select()
    select.meetGreet()
    
    # Select guest details
    select = search.guests.select()
    select.email()
    select.phone()
    
    # Select property details
    select = search.properties.select()
    select.weClean()
    
    # Select manager details
    select = search.propertyManagers.select()
    select.name()
    select.email()  # Changed from company_email
    
    # Apply additional conditions
    set_valid_management_booking(search)
    
    where = search.properties.where()
    where.weClean().isEqualTo(weClean)
    
    return search.fetchall()


#######################################################
# EMAIL FUNCTIONS
#######################################################

def send_new_management_arrivals_email(
        bookings: list[Booking], 
        start: date, 
        end: date, 
        daily: bool) -> None:
    """
    Create and send an email to the property manager about upcoming arrivals.
    
    Args:
        bookings: List of bookings to include in the email
        start: The start date for the email date range
        end: The end date for the email date range
        daily: Whether this is a daily update email
        
    Returns:
        None
    """
    subject = get_subject('ARRIVALS', start, end, daily)
    to = determine_manager_email(bookings[0])
    name = determine_manager_name(bookings[0])
    user, message = new_internal_email(subject=subject, to=to, name=name)
    body = message.body
    
    for booking in bookings:
        body.separation()
        if booking.arrival.isSoon:
            body.paragraph(f'This is a NEW BOOKING for <b>{booking.arrival.prettyDate}</b>!')
        body.table(get_booking_table_data(booking, **get_kwargs_for_table()))
    
    message.send()


def get_kwargs_for_table() -> dict[str, bool]:
    """
    Returns keyword arguments for booking table data configuration.
    
    Returns:
        Dictionary of options for table display settings
    """
    return {
        'cleanInfo': True,
        'meetGreetInfo': True,
        'guestContactInfo': True,
        'extrasInfo': True,
    }