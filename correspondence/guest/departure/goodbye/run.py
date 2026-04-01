from apis.google.mail.message import GoogleMailMessage
from correspondence.guest.departure.functions import (
    get_guest_departure_email_bookings,
    new_guest_departure_email
)
from correspondence.guest.functions import send_guest_email
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.guest.functions import guest_has_stayed_before
from default.google.mail.functions import valid_email_address
from default.settings import WEBSITE_LINK
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_goodbye_emails(
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None) -> str:
    """
    Send goodbye emails to guests who have completed their stays.
    
    Args:
        start: Starting date for departure range
        end: Ending date for departure range
        emailSent: Filter by whether email has already been sent
        bookingId: Specific booking ID to send reminder for
        
    Returns:
        Status message indicating success or no emails to send
    """
    if start is None and end is None: 
        start, end = updatedates.goodbye_emails_dates()
    
    database = get_database()
    bookings = get_goodbye_bookings(database, start, end, emailSent, bookingId)
    
    if not bookings: 
        database.close()
        return 'NO new emails to send.'
    
    for booking in bookings:
        guestEmail = booking.guest.email
        if valid_email_address(address=guestEmail):
            if guestEmail not in booking.property.owner.email:
                new_goodbye_email(booking, bookingId)
        
        # Update email status
        booking.emails.goodbye = True
        booking.update()
    
    database.close()
    return 'All emails sent!'


def get_goodbye_bookings(
    database: Database, 
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None) -> list[Booking]:
    """
    Retrieves bookings for goodbye emails with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering departures
        end: The end date for filtering departures
        emailSent: Whether goodbye email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_guest_departure_email_bookings(
                                            database, 
                                            start=start, 
                                            end=end, 
                                            bookingId=bookingId)
    
    # Select arrival date
    select = search.arrivals.select()
    select.meetGreet()
    
    # Select booking details
    select = search.details.select()
    select.isOwner()
    
    # Apply email conditions if not filtering by bookingId
    if not bookingId:
        where = search.emails.where()
        where.goodbye().isEqualTo(emailSent)

        where = search.arrivals.where()
        where.meetGreet().isTrue()
    
    return search.fetchall()


def new_goodbye_email(booking: Booking, bookingId: int = None) -> None:
    """
    Create and send a goodbye email to a guest.
    
    Args:
        booking: The booking containing guest and property information
        bookingId: The ID of the booking
        
    Returns:
        None
    """
    user, message = new_guest_departure_email(topic='Thank you to', booking=booking)
    body = message.body

    wonderful_time(body, booking)
    thank_you(body)
    feedback(body)
    if guest_has_stayed_before(booking):
        if booking.property.isQuintaDaBarracuda:
            google_review(body)
            google_link(body)
    book_again(body)
    website_link(body)

    send_guest_email(user, message, bookingId)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def wonderful_time(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add personal greeting and hope that guest had a wonderful time.
    
    Args:
        body: The email body to append text to
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        f'I do hope that you had a wonderful time at {booking.property.name}!',
    )


def thank_you(body: GoogleMailMessage.Body) -> None:
    """
    Add thank you message to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'On behalf of Algarve Beach Apartments, I would like to take this',
        'opportunity to thank you for choosing us. It was a privilege to be able',
        'to provide you with our accommodation and services over these last days.',
        'We hope that we have lived up to your expectations and helped to create',
        'a memorable holiday experience.'
    )


def feedback(body: GoogleMailMessage.Body) -> None:
    """
    Add message requesting guest feedback.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'As part of our continuous commitment to improving our services, your',
        'feedback is very important to us. If you have a moment, we would',
        'greatly appreciate your thoughts on your stay with us.',
    )


def google_review(body: GoogleMailMessage.Body) -> None:
    """
    Add message requesting a Google review from returning guests.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'As you are now a returning guest, if you would like to leave a review',
        'of your experience with us on Google that would be particularly',
        'appreciated.'
    )


def google_link(body: GoogleMailMessage.Body) -> None:
    """
    Add Google review link to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.link(
        'https://g.page/r/CS9FnSWnIAWtEBM/review',
        'Click here to add a Google review',
    )


def book_again(body: GoogleMailMessage.Body) -> None:
    """
    Add message encouraging guests to book again.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'If you are considering returning to the Algarve in the future, it would',
        'be our pleasure to assist you once again. Please feel free to get in',
        'touch with us directly.',
    )


def website_link(body: GoogleMailMessage.Body) -> None:
    """
    Add website link to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.link(
        WEBSITE_LINK,
        WEBSITE_LINK,
        centre=True,
    )