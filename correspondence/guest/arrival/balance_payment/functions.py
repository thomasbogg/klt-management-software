from datetime import date

from correspondence.guest.arrival.functions import get_guest_arrival_email_bookings
from default.booking.booking import Booking
from default.database.database import Database


def get_balance_payment_bookings(
    database: Database, 
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None
) -> list[Booking]:
    """
    Retrieve bookings that need balance payment processing.
    
    Gets bookings within a date range that are direct bookings (not from 
    external platforms) and filters based on whether balance payment emails 
    have been sent.
    
    Args:
        database: The database connection object.
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.
        emailSent: Whether to include bookings where balance payment emails have been sent.
        bookingId: Optional specific booking ID to filter by.
        
    Returns:
        A list of Booking objects that match the criteria.
    """
    search = get_guest_arrival_email_bookings(database, start=start, end=end, bookingId=bookingId)
    
    # Select fields
    select = search.details.select()
    select.PIMSId()
  
    select = search.charges.select()
    select.basicRental()
    select.admin()
    select.currency()
  
    select = search.forms.select()
    select.balancePayment()
    select.PIMSuin()
    select.PIMSoid()
  
    # Set search criteria
    where = search.details.where()
    where.isOwner().isFalse()
    where.enquirySource().isEqualTo("Direct")
  
    if not bookingId:
        where = search.emails.where()
        where.balancePayment().isEqualTo(emailSent)
  
    return search.fetchall()