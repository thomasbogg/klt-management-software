from apis.google.account import GoogleAccount
from apis.google.mail.message import GoogleMailMessage
from correspondence.functions import get_email_bookings
from correspondence.internal.functions import (
    get_subject,
    new_internal_email
)
from datetime import date
from default.database.database import Database
from default.database.functions import set_valid_accounts_booking


#######################################################
# EMAIL DATA RETRIEVAL FUNCTIONS
#######################################################

def get_accountancy_email_bookings(
        database: Database, 
        bookingId: int = None, 
        noBlocks: bool = True):
    """
    Retrieves accountancy email bookings with specified conditions.

    Args:
        database: The database connection object
        bookingId: The specific booking ID to filter by
        noBlocks: Whether to exclude block bookings

    Returns:
        A search object with the selected data and applied conditions
    """
    # Initialize search using the higher-level function
    search = get_email_bookings(database, bookingId, noBlocks=noBlocks)
    
    # Select booking details
    select = search.details.select()
    select.enquirySource()
    
    # Select arrival date
    select = search.arrivals.select()
    select.date()
    
    # Apply accountancy-specific conditions
    where = search.details.where()
    where.isOwner().isFalse()
    
    set_valid_accounts_booking(search)
    return search


#######################################################
# EMAIL CREATION FUNCTIONS
#######################################################

def new_accountancy_email(
        account: GoogleAccount = None, 
        topic: str = None, 
        start: date = None, 
        end: date = None, 
        daily: bool = False) -> GoogleMailMessage:
    """
    Creates a new accountancy email message.
    
    Args:
        account: The Google account to use for sending the email
        topic: The topic of the email
        start: The start date for the email date range
        end: The end date for the email date range
        daily: Whether this is a daily update email
        
    Returns:
        A Google Mail message object configured for accountancy emails
    """
    to = 'kevin@algarvebeachapartments.com'
    name = 'Dad'
    subject = get_subject(topic, start, end, daily)
    return new_internal_email(account=account, to=to, name=name, subject=subject)