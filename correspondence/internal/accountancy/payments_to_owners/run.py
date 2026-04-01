from correspondence.internal.accountancy.functions import (
    get_accountancy_email_bookings,
    new_accountancy_email
)
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.mail.functions import send_email
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_payments_to_owners_email(
        start: date = None, 
        end: date = None, 
        daily: bool = True, 
        emailSent: bool = False) -> str:
    """
    Send email notification about payments to property owners.
    
    Args:
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        daily: Whether this is a daily update email
        emailSent: Filter by whether email has already been sent
        
    Returns:
        Status message indicating success or no payments to report
    """
    if start is None and end is None: 
        start, end = updatedates.payments_to_owners_email_dates()
    
    database = get_database()
    bookings = get_payments_to_owners_bookings(database, start, end, emailSent)
    
    if not bookings: 
        database.close()
        return f'NO PAYMENTS TO OWNERS for period {start} TO {end}. Skipping email.'
    
    new_payments_to_owners_email(bookings, start, end, daily)
    
    for booking in bookings: 
        booking.emails.payOwner = True
        booking.update()
    
    database.close()
    return 'Payments Email successfully sent!'


def get_payments_to_owners_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        bookingId: int = None, 
        noBlocks: bool = True) -> list[Booking]:
    """
    Retrieves payments to owners booking data with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether payment to owners email has been sent
        bookingId: The specific booking ID to filter by
        noBlocks: Whether to exclude block bookings

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_accountancy_email_bookings(database, bookingId=bookingId, noBlocks=noBlocks)
    
    # Select property details
    select = search.properties.select()
    select.shortName()
    
    # Select details from the bookings table
    select = search.details.select()
    select.enquirySource()
    
    # Apply date range conditions
    where = search.arrivals.where()
    where.date().isGreaterThanOrEqualTo(start)
    where.date().isLessThanOrEqualTo(end)
    
    # Apply email conditions
    where = search.emails.where()
    where.payOwner().isEqualTo(emailSent)
    
    return search.fetchall()


#######################################################
# EMAIL CREATION FUNCTIONS
#######################################################

def new_payments_to_owners_email(
        bookings: list[Booking], 
        start: date, 
        end: date, 
        daily: bool) -> None:
    """
    Create and send an email about payments to property owners.
    
    Args:
        bookings: List of bookings requiring owner payments
        start: The start date for the email date range
        end: The end date for the email date range
        daily: Whether this is a daily update email
        
    Returns:
        None
    """
    user, message = new_accountancy_email(
        topic='PAYMENTS TO OWNERS', 
        start=start, 
        end=end, 
        daily=daily
    )
    
    body = message.body
    body.paragraph(f'There are {len(bookings)} payments to owners:', underlined=True)
    
    count = 1
    for booking in bookings:
        paymentLine = [f'<b>{count})</b> {booking.guest.fullName}']
        paymentLine += [f'in {booking.property.shortName}']
        paymentLine += [f'arrived {booking.arrival.prettyDate}']
     
        if booking.property.name == 'Parque da Corcovada':
            if booking.details.enquirySource == 'Direct':    
                paymentLine += ['- <b>PAY UK ACCOUNT</b>']
     
        body.paragraph(' '.join(paymentLine))
        count += 1

    send_email(user, message)
