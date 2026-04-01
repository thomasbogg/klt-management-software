from datetime import date

from apis.google.mail.message import GoogleMailMessage
from correspondence.owner.functions import get_owner_email_bookings, new_owner_email
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.forms.functions import get_form_responder_uri
from default.google.mail.functions import send_email
from default.update.dates import updatedates
from default.update.wrapper import update
from forms.arrival.owner.functions import set_owner_arrival_form


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_owner_four_weeks_emails(
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        bookingId: int = None) -> str:
    """
    Send emails to property owners with four-week arrival questionnaires.
    
    Args:
        start: Starting date for arrival range
        end: Ending date for arrival range
        emailSent: Filter by whether email has already been sent
        bookingId: Specific booking ID to send questionnaire for
        
    Returns:
        Status message indicating success or no emails to send
    """
    if start is None and end is None: 
        start, end = updatedates.four_weeks_emails_dates()
    
    database = get_database()
    bookings = get_four_weeks_bookings(database, start, end, emailSent, bookingId)
    
    if not bookings: 
        database.close()
        return 'NO new emails to send.'
    
    doneProperties = list()
    for booking in bookings:
        if booking.property.name in doneProperties: 
            continue
        doneProperties.append(booking.property.name)
        send_new_owner_four_weeks_email(booking)
        
        # Update email status
        booking.emails.arrivalQuestionnaire = True
        booking.update()
    
    database.close()
    return 'All emails sent!'


def get_four_weeks_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves owner bookings for the four weeks questionnaire with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether questionnaire email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A list of Booking objects that match the criteria
    """
    # Initialize search using the higher-level function
    search = get_owner_email_bookings(database, start=start, end=end, bookingId=bookingId)
    
    # Select enquiry date
    select = search.details.select()
    select.enquiryDate()
    select.isOwner()
    
    # Select forms details
    # Note: 'four_weeks' is now part of arrivalQuestionnaire
    select = search.forms.select()
    select.id()
    select.arrivalQuestionnaire()

    # Select from properties
    select = search.properties.select()
    select.weClean()

    # Select from properties specs
    select = search.propertySpecs.select()
    select.bedrooms()

    # Apply property conditions - owner booking forms required
    where = search.properties.where()
    where.sendOwnerBookingForms().isTrue()
    
    # Apply flight conditions if not looking for a specific booking
    if not bookingId:
        # Check for missing flight information
        where = search.arrivals.where()
        where.flightNumber().isNullEmptyOrFalse()
        where.details().isNullEmptyOrFalse()
        
        # Apply email conditions
        where = search.emails.where()
        where.arrivalQuestionnaire().isEqualTo(emailSent)
    
    return search.fetchall()


def send_new_owner_four_weeks_email(booking: Booking) -> None:
    """
    Create and send a four weeks questionnaire email to the property owner.
    
    Args:
        booking: The booking containing property and owner information
        
    Returns:
        None
    """
    user, message = new_owner_email(subject=subject(booking), booking=booking)    
    body = message.body
    
    salutation(body)
    introduction(body, booking)
    options(body)
    explainer(body)
    form(body)
    link(body, booking)
    conclusion(body)
    
    send_email(user, message, checkSent=True)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def subject(booking: Booking) -> str:
    """
    Generate the email subject line.
    
    Args:
        booking: The booking object containing arrival and departure dates
        
    Returns:
        A formatted subject line string
    """
    return ' '.join([
        'Mandatory Arrival Form for Owner Booking -',
        f'START: {booking.arrival.prettyDate};',
        f'END: {booking.departure.prettyDate}'
    ])


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


def introduction(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add introduction paragraph about the arrival form.
    
    Args:
        body: The email body to append text to
        booking: The booking containing arrival information
        
    Returns:
        None
    """
    body.paragraph(
        f'As we are approaching the arrival date, <b>{booking.arrival.prettyDate}</b>, for the',
        f'booking made at your request on {booking.details.prettyEnquiryDate}, in',
        f'<b>{booking.property.name}</b>, I am now sending you an arrival form that',
        'will help us understand your needs and/or those of your guests. We sincerely appreciate',
        'you taking the time to give us as much information as possible.',
    )


def explainer(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation about what information is needed in the form.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'Among other things, the form checks <u>the requirement of a meet & greet and',
        'a post-stay clean for this booking</u>. It also asks you to provide the contact details of your',
        'guests and their arrival/departure times or, if the booking is for you, your own arrival/departure day plans.',
        'Thirdly, it offers the chance to order optional extras such as children\'s cots and',
        'chairs, airport transfer services, food packs, etc., either for you or for your guest.',
        'Finally, there is a section for custom comments to make clear anything not covered by the',
        'previous sections.'
    )


def options(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions about filling out the form.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        '<b>Whether this booking is for you or a guest of yours, please still open the form and fill',
        'out as much as possible.</b>',
    )


def form(body: GoogleMailMessage.Body) -> None:
    """
    Add form introduction text to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'This is the form. Please open and answer all required fields:',
    )


def link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add the form link to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking containing form information
        
    Returns:
        None
    """
    formId = booking.forms.arrivalQuestionnaire
    if not formId:
        formId = set_owner_arrival_form(booking)
    
    responderUri = get_form_responder_uri(formId)
    body.link(
        responderUri,
        f'Owner Booking Arrival Form for {booking.property.owner.name}'
    )


def conclusion(body: GoogleMailMessage.Body) -> None:
    """
    Add closing paragraph to the email body.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'I trust that this has been helpful. If you have any questions, I am always available.'
    )