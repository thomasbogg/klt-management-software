from apis.google.account import GoogleAccount
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import get_email_bookings
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.google.mail.functions import new_email
from default.property.property import Property
from default.settings import VALID_BOOKING_STATUSES


#######################################################
# EMAIL CREATION FUNCTIONS
#######################################################

def new_owner_email(
        account: GoogleAccount = None, 
        subject: str = None, 
        booking: Booking = None, 
        property: Property = None) -> tuple[GoogleMailMessages, GoogleMailMessage]:
    """
    Creates a new email message for the property owner.
    
    Args:
        account: The Google account to use for sending the email
        subject: The subject of the email
        booking: The booking object associated with the email
        property: The property object associated with the email
        
    Returns:
        A tuple containing the user and the email message
    """
    if booking:
        property = booking.property
    return new_email(
                    account=account, 
                    subject=subject, 
                    to=property.owner.email, 
                    name=property.owner.name.split()[0]
    )


#######################################################
# DATABASE QUERY FUNCTIONS
#######################################################

def get_owner_email_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        bookingId: int = None) -> Database:
    """
    Retrieves owner email bookings with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        bookingId: The specific booking ID to filter by

    Returns:
        A search object with the selected data and applied conditions
    """
    # Initialize search using the higher-level function
    search = get_email_bookings(database, bookingId=bookingId, noBlocks=True)
    
    # Select arrival and departure dates
    select = search.arrivals.select()
    select.date()
    
    select = search.departures.select()
    select.date()
    
    # Select owner details
    select = search.propertyOwners.select()
    select.name()
    select.email()
    
    # Apply booking conditions
    where = search.details.where()
    where.isOwner().isTrue()  # Changed from owner_booking=True
    where.enquiryStatus().isIn(VALID_BOOKING_STATUSES)
    
    if bookingId is None and (start or end):
        # Apply date conditions if no specific bookingId
        where = search.arrivals.where()
        where.date().isGreaterThanOrEqualTo(start)
        where.date().isLessThanOrEqualTo(end)
    
    # Set pause_emails condition to check paused column
    where = search.emails.where()
    where.paused().isFalse()
    
    return search