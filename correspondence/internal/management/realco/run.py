from datetime import date

from apis.google.mail.message import GoogleMailMessage
from correspondence.internal.functions import (
    get_booking_table_data,
    get_subject,
    new_internal_email
)
from correspondence.internal.management.functions import get_management_email_bookings
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database,
    set_valid_management_booking
)
from default.google.mail.functions import send_email
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_realco_email(start: date = None, end: date = None) -> str:
    """
    Send email to Realco about upcoming arrivals within specified date range.
    
    Creates and sends an email containing information about upcoming arrivals
    at Clube do Monaco properties to Realco management.
    
    Args:
        start: The start date for filtering arrivals. If None, uses default dates.
        end: The end date for filtering arrivals. If None, uses default dates.
        
    Returns:
        A message indicating successful completion or that no emails were sent.
    """
    if start is None and end is None: 
        start, end = updatedates.realco_email_dates()
    
    database = get_database()
    bookings = get_realco_email_bookings(database, start, end)
    
    if not bookings: 
        database.close()
        return 'Got no emails to send'
    
    _send_new_realco_email(bookings, start, end)
    
    database.close()
    return 'Successfully sent email to Realco!'


def get_realco_email_bookings(database: Database, start: date = None, 
                             end: date = None) -> list[Booking]:
    """
    Retrieve Realco email bookings with specified conditions.

    Gets bookings for Clube do Monaco properties with valid status within
    the specified date range.
    
    Args:
        database: The database connection object.
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.

    Returns:
        A list of Booking objects that match the criteria.
    """
    search = get_management_email_bookings(database, start=start, end=end, emailSent=True)
    
    set_valid_management_booking(search)
    
    where = search.properties.where()
    where.name().isLike("Clube do Monaco")
    
    return search.fetchall()


#######################################################
# EMAIL FUNCTIONS
#######################################################

def _send_new_realco_email(bookings: list[Booking], start: date, end: date) -> None:
    """
    Create and send email to Realco with booking information.
    
    Args:
        bookings: List of bookings to include in the email.
        start: The start date of the date range being reported.
        end: The end date of the date range being reported.
        
    Returns:
        None
    """
    subject = get_subject('UPCOMING ARRIVAL', start, end, daily=False)
    user, message = new_internal_email(to='realco@sapo.pt', name='Paula', subject=subject)
    body = message.body
    
    _opening(body)
    
    for booking in bookings:
        body.separation()
        body.table(get_booking_table_data(booking))
    
    _closing(body)
    send_email(user, message, True)


def _opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this finds you well. I am emailing you the latest expected arrivals',
        'for the dates shown in the subject of this email.'
    )


def _closing(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I trust this has been helpful. Please let me know if you have questions.'
    )