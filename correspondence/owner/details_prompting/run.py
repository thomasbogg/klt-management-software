from correspondence.owner.functions import get_owner_email_bookings, new_owner_email
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
def send_arrival_details_prompting_emails(
        start: date = None, 
        end: date = None, 
        bookingId: int = None) -> str:
    """
    Send emails to property owners prompting for missing arrival details.
    
    Args:
        start: Starting date for arrival range
        end: Ending date for arrival range
        bookingId: Specific booking ID to send prompt for
        
    Returns:
        Status message indicating success or no emails to send
    """
    if start is None and end is None: 
        start, end = updatedates.arrival_details_prompting_emails_dates()
    
    database = get_database()
    bookings = get_details_prompting_bookings(database, start, end, bookingId)
    
    if not bookings: 
        database.close()
        return 'NO new prompt emails to send.'
    
    for booking in bookings:
        if not booking.arrival.meetGreet: 
            continue
            
        if booking.property.shortName == 'B11':
            # Removed commented out code about ManagementPromptingEmail
            continue
            
        if booking.arrival.date in updatedates.owner_prompting_dates(): 
            send_new_owner_prompting_email(booking)
    
    database.close()
    return 'All emails sent!'


def get_details_prompting_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves owner bookings that need details prompting.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_owner_email_bookings(database, start=start, end=end, bookingId=bookingId)
    
    # Select booking enquiry date
    select = search.details.select()
    select.enquiryDate()
    
    # Select arrival meet and greet
    select = search.arrivals.select()
    select.meetGreet()
    
    # Apply property conditions
    where = search.properties.where()
    where.sendOwnerBookingForms().isFalse()
    
    # Apply arrival conditions - checking for missing flight information
    where = search.arrivals.where()
    where.flightNumber().isNullEmptyOrFalse()
    where.details().isNullEmptyOrFalse()
    
    return search.fetchall()


def send_new_owner_prompting_email(booking: Booking) -> None:
    """
    Create and send an email to the property owner requesting missing arrival details.
    
    Args:
        booking: The booking containing property and arrival information
        
    Returns:
        None
    """
    user, message = new_owner_email(subject=subject(booking), booking=booking)
    body = message.body
    
    salutation(body)
    introduction(body, booking)
    explainer(body)
    information_1(body)
    information_2(body)
    conclusion(body)
    
    send_email(user, message)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def subject(booking: Booking) -> str:
    """
    Generate the email subject line.
    
    Args:
        booking: The booking object containing arrival information
        
    Returns:
        A string containing the formatted subject line
    """
    return (
        f'Missing Arrival Information for Booking {booking.arrival.prettyDate} in {booking.property.shortName}'
    )


def salutation(body) -> None:
    """
    Add salutation to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this finds you well.'
    )


def introduction(body, booking: Booking) -> None:
    """
    Add introduction paragraph about the missing arrival information.
    
    Args:
        body: The email body to append text to
        booking: The booking containing arrival information
        
    Returns:
        None
    """
    body.paragraph(
        f'As we are approaching the arrival date, <b>{booking.arrival.prettyDate}</b>, for the booking',
        f'made at your request in <b>{booking.property.name}</b>, I am sending you a reminder',
        'about <u>missing arrival information</u>.',
    )


def explainer(body) -> None:
    """
    Add explanation about what information is needed from the guest.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'Please contact the guest at the earliest available opportunity and ask them for their arrival and '
        'departure day plans. When you have the details, just reply to this email with them, and I will take',
        'care of the rest.',
    )


def information_1(body) -> None:
    """
    Add specific details about arrival information needed.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'The information we need is the inbound flight number, its arrival time and whether',
        'they are landing at Faro or Lisbon airport. If they are not flying to the Algarve but',
        'are arriving by some other form of transport (car, coach, train), we need to have',
        'their estimated arrival time at the property.',
    )


def information_2(body) -> None:
    """
    Add specific details about departure information needed.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'And the same information for their departure, i.e. outbound flight number, takeoff',
        'time and which airport. Again, if they are not flying out of the Algarve, we need',
        'information on their departure plans and their estimated departure time from',
        'the property.',
    )


def conclusion(body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'This is just a reminder that this information is outstanding. I will continue to',
        'monitor the situation, but since we\'re approaching critical dates, your assistance',
        'would be greatly appreciated.',
    )