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
    set_valid_management_booking
)
                                        
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_management_cleans_emails(
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        weClean: bool = True, 
        bookingId: int = None) -> str:
    """
    Send email notifications to cleaning managers about upcoming cleans.
    
    Args:
        start: Starting date for arrival range
        end: Ending date for arrival range
        emailSent: Filter by whether email has already been sent
        weClean: Filter for properties we clean
        bookingId: Specific booking ID to send information about
        
    Returns:
        Status message indicating success or no bookings to report
    """
    if start is None and end is None: 
        start, end = updatedates.management_cleans_emails_dates()
    
    database = get_database()
    bookings = get_management_cleans_email_bookings(database, start, end, emailSent, weClean, bookingId)
    
    if not bookings: 
        database.close()
        return 'Got no bookings to send to cleaning manager!'
    
    send_new_management_cleans_email(bookings, start, end, daily=True)
    
    for booking in bookings:
        # Update email status
        booking.emails.management = True
        booking.update()
    
    database.close()
    return 'All emails to cleaning managers sent!'


def get_management_cleans_email_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        weClean: bool = True, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves management cleans email bookings with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether management clean email has been sent
        weClean: Whether to filter for properties we clean
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_management_email_bookings(database, start=start, end=end, emailSent=emailSent, bookingId=bookingId)
    
    # Select property manager details
    select = search.propertyManagers.select()
    select.cleaning()
    select.cleaningEmail()
    
    # Select property details
    select = search.properties.select()
    select.weClean()
    
    # Apply additional conditions
    set_valid_management_booking(search)
    
    where = search.properties.where()
    where.weClean().isEqualTo(weClean)
    
    return search.fetchall()


#######################################################
# EMAIL FUNCTIONS
#######################################################

def send_new_management_cleans_email(
        bookings: list[Booking], 
        start: date, 
        end: date, 
        daily: bool) -> None:
    """
    Create and send an email to the cleaning manager about upcoming cleans.
    
    Args:
        bookings: List of bookings to include in the email
        start: The start date for the email date range
        end: The end date for the email date range
        daily: Whether this is a daily update email
        
    Returns:
        None
    """
    subject = get_subject('UPCOMING ARRIVALS', start, end, daily)
    to = determine_manager_email(bookings[0])
    name = determine_manager_name(bookings[0])
    user, message = new_internal_email(subject=subject, to=to, name=name)
    body = message.body
    
    for booking in bookings:
        cleanInfo = False
        body.separation()
        if booking.details.isOwner:
            cleanInfo = True

            if booking.arrival.isVerySoon:
                body.paragraph(f'This is a NEW OWNER BOOKING!')
            else:
                body.paragraph(f'This is an OWNER BOOKING!')

        elif booking.arrival.isVerySoon:
            body.paragraph(f'This is a NEW booking!')
        body.table(get_booking_table_data(booking, cleanInfo=cleanInfo, extrasInfo=True))
    
    message.send()