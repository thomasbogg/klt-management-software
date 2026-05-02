from accounts.accounts import TeamAtABA
from apis.google.mail.message import GoogleMailMessage
from correspondence.guest.arrival.functions import (
    get_arrival_table_data,
    new_guest_arrival_email
)
from correspondence.guest.arrival.instructions.functions import (
    check_discrepancies,
    closing,
    get_arrival_instructions_bookings,
    get_changeover_bookings,
    send_new_arrival_instructions_email
)
from correspondence.guest.functions import send_guest_email
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.mail.functions import valid_email_address
from default.update.dates import updatedates
from default.update.wrapper import update


@update
def send_two_days_instructions_emails(
    start: date = None, 
    end: date = None, 
    bookingId: int = None
) -> str:
    """
    Send check-in instruction emails to guests arriving in two days.
    
    Args:
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        bookingId: Optional specific booking ID to process
        
    Returns:
        str: Status message indicating success or no emails to send
    """
    if not bookingId and start is None and end is None:
        start, end = updatedates().check_in_information_emails_dates()
    
    database = get_database()
    bookings = get_check_in_instructions_bookings(
                                                database, 
                                                start=start, 
                                                end=end, 
                                                bookingId=bookingId)
    
    if not bookings:
        database.close()
        return 'NO new emails to send.'
    
    for booking in bookings:
        if not booking.arrival.meetGreet:
            continue
            
        emailAddress = booking.guest.email
        if not emailAddress:
            continue
            
        if not valid_email_address(booking):
            continue
            
        if not booking.arrival.hasDetails:
            if booking.property.shortName == 'B11':
                continue
            if booking.details.isPlatform:
                continue
            if not booking.forms.arrivalQuestionnaire:
                continue

        changeoverBookings = get_changeover_bookings(
                                                database, 
                                                date=booking.arrival.date, 
                                                guestId=booking.guest.id)
            
        if changeoverBookings:
            prevProperty = changeoverBookings[0].property.name
            if prevProperty != booking.property.name:
                send_new_apartment_changeover_email(
                    booking, prevProperty, bookingId)
        else:
            send_new_arrival_instructions_email(
                account=TeamAtABA(), 
                topic='Check-in Instructions', 
                booking=booking, 
                bookingId=bookingId, 
                twoWeeks=False
            )
        
        booking.emails.checkInInstructions = True
        booking.update()
    
    database.close()
    return 'All emails sent!'


def get_check_in_instructions_bookings(database: Database, start: date = None, 
                                      end: date = None, 
                                      bookingId: int = None) -> list[Booking]:
    """
    Retrieve bookings that need check-in instruction emails.
    
    Args:
        database: Database connection
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        bookingId: Optional specific booking ID to retrieve
        
    Returns:
        list[Booking]: Bookings that need check-in instruction emails
    """
    search = get_arrival_instructions_bookings(
        database, start=start, end=end, bookingId=bookingId)
        
    if bookingId is None:
        where = search.emails.where()
        where.checkInInstructions().isFalse()
    
    where = search.properties.where()
    where.weClean().isTrue()
    
    return search.fetchall()


# Email creation functions
def send_new_apartment_changeover_email(booking: Booking, previous: str, 
                                       bookingId: int = None) -> None:
    """
    Send an email to a guest who is changing apartments during their stay.
    
    Args:
        booking: Booking object for the new apartment
        previous: Name of the previous apartment
        bookingId: Optional booking ID for tracking
        
    Returns:
        None
    """
    user, message = new_guest_arrival_email(
        TeamAtABA(), 'Change of Apartment', booking)
    body = message.body
    
    changeover_opening(body, booking)
    explainer(body)
    this_leg(body)
    body.table(get_arrival_table_data(booking, addTravel=False, addExtras=False))
    check_discrepancies(body, twoWeeks=False)
    meet_at_old_apartment(body, previous)
    meeting_time(body)
    being_ready(body)
    moving(body)
    closing(body)
    wish_you(body)
    
    send_guest_email(user, message, bookingId)
    return None


# Email section functions
def changeover_opening(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add opening paragraph mentioning the apartment change date.
    
    Args:
        body: Email body to modify
        booking: Booking with changeover details
        
    Returns:
        None
    """
    body.paragraph(
        f'You will be changing apartment on {booking.arrival.prettyDate}'
    )


def explainer(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph explaining the purpose of the email.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'The purpose of this email is to explain the changeover procedure.',
        bold=True
    )    


def this_leg(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph introducing the booking details section.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'This leg of your holiday is based on the following details:'
    )


def meet_at_old_apartment(body: GoogleMailMessage.Body, previous: str) -> None:
    """
    Add paragraph explaining where to meet for the changeover.
    
    Args:
        body: Email body to modify
        previous: Name of the previous apartment
        
    Returns:
        None
    """
    body.paragraph(
        'On the day of the changeover we will meet you at the door of the apartment',
        f'you are checking out of - in this case {previous}.'
    )
            
            
def meeting_time(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph explaining the meeting time for changeover.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We would normally aim to be there some time between 11.00 and 12.00.',
        'You may have already agreed a time with us during the original Meet & Greet.',
        'But if you haven\'t, or would like a different time, please feel free to reply',
        'to this email at your earliest convenience.',
    )


def being_ready(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph requesting guests to be ready for changeover.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We kindly ask that you are packed and ready to leave as soon as we arrive.',
        'On an average day, we deal with multiple check-ins and check-outs and we',
        'pride ourselves on our ability to be with everyone in good time.',
    )


def moving(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph explaining the apartment changeover process.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Once with you, we will help move your belongings to the new apartment.',
        'We will also give you a brief tour of it, hand over the keys and point',
        'out the more glaring differences - if any - between the two places.'
    )


def wish_you(body: GoogleMailMessage.Body) -> None:
    """
    Add closing well-wishes for the guest's continued holiday.
    
    Args:
        body: Email body to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Wish you a fabulous continuation of your holiday!'
    )