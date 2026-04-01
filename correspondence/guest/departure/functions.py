from datetime import date

from apis.google.account import GoogleAccount
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.functions import (
    get_guest_email_bookings,
    new_guest_email
)
from default.booking.booking import Booking
from default.database.database import Database


def new_guest_departure_email(
    account: GoogleAccount = None,
    topic: str = None,
    booking: Booking = None
) -> tuple[GoogleMailMessages, GoogleMailMessage]:
    """
    Create a new email for guest departure communication.
    
    Args:
        account: The Google account to use for sending the email
        topic: The topic of the email
        booking: The booking object containing guest information
        
    Returns:
        A tuple containing the email service and message objects
    """
    subject = f'{topic} {booking.guest.lastName} in {booking.property.name}'
    return new_guest_email(account=account, subject=subject, booking=booking)


def get_guest_departure_email_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    bookingId: int = None
) -> Database:
    """
    Retrieve bookings for guest departure emails within a date range.
    
    Args:
        database: The database connection object
        start: The start date for filtering departures
        end: The end date for filtering departures
        bookingId: Optional specific booking ID to retrieve
        
    Returns:
        A database search object ready for further filtering
    """
    search = get_guest_email_bookings(database, bookingId=bookingId)

    select = search.departures.select()
    select.date()
    
    select = search.properties.select()
    select.weClean()
    
    select = search.propertyOwners.select()
    select.email()
    
    if not bookingId:
        where = search.departures.where()
        if start:
            where.date().isGreaterThanOrEqualTo(start)
        if end:
            where.date().isLessThanOrEqualTo(end)
    
    return search