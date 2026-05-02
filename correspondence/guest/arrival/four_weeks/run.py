from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.arrival.functions import (
    get_guest_arrival_email_bookings,
    new_guest_arrival_email
)
from correspondence.guest.functions import send_guest_email
from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import get_database
from default.google.forms.functions import get_form_responder_uri
from default.google.mail.functions import valid_email_address
from default.update.dates import updatedates
from default.update.wrapper import update
from forms.arrival.guest.functions import set_guest_arrival_form
from platforms.airbnb.browser import BrowseAirbnb
from web.browser import Browser


@update
def send_guest_four_weeks_emails(
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None
) -> str:
    """
    Send reminder emails to guests four weeks before their arrival.
    
    Sends emails or Airbnb messages to guests with arrival information request.
    For non-Airbnb bookings, sends email with a questionnaire link. For Airbnb
    bookings, sends a message through Airbnb's messaging system.
    
    Args:
        start: The start date for filtering arrivals. If None, uses default dates.
        end: The end date for filtering arrivals. If None, uses default dates.
        emailSent: Whether to include bookings where emails have already been sent.
        bookingId: Optional specific booking ID to process.
        
    Returns:
        A message indicating the outcome of the email sending operation.
    """
    if not bookingId and start is None and end is None: 
        start, end = updatedates.four_weeks_emails_dates()
    
    database: Database = get_database()
    bookings: list[Booking] = get_four_weeks_bookings(
                                                    database, 
                                                    start, 
                                                    end, 
                                                    emailSent,                                                 
                                                    bookingId)

    if not bookings: 
        database.close()
        return 'NO new emails to send.'

    airbnbBookings: list[Booking] = list()
    
    for booking in bookings:
        if booking.details.platformId is None: 
            continue
            
        guestEmail: str = booking.guest.email
        source: str = booking.details.enquirySource
       
        if guestEmail: 
            if valid_email_address(booking): 
                _send_new_guest_four_weeks_email(
                                                booking=booking, 
                                                html=True, 
                                                bookingId=bookingId)
                booking.emails.arrivalQuestionnaire = updatedates.date()
                booking.emails.update()

        elif source == 'Airbnb': 
            if booking.details.platformId:
                airbnbBookings.append(booking)            

    if airbnbBookings: 
        _send_airbnb_messages(airbnbBookings)

    database.close()
    return 'All emails sent!'


def get_four_weeks_bookings(
    database: Database, 
    start: date = None, 
    end: date = None, 
    emailSent: bool = False, 
    bookingId: int = None
) -> list[Booking]:
    """
    Retrieve bookings for four-week arrival reminder emails.
    
    Gets bookings within the date range that need arrival information with
    appropriate filters for email status and booking type.
    
    Args:
        database: The database connection object.
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.
        emailSent: Whether to include bookings where emails have already been sent.
        bookingId: Optional specific booking ID to filter by.
        
    Returns:
        A list of Booking objects that match the criteria.
    """
    search = get_guest_arrival_email_bookings(
                                            database, 
                                            start=start, 
                                            end=end, 
                                            bookingId=bookingId)

    # Select columns from the owners table
    select = search.propertyOwners.select()
    select.name()
    
    # Select columns from the forms table
    select = search.forms.select()
    select.id()
    select.arrivalQuestionnaire()

    # Select from the properties table
    select = search.properties.select()
    select.weClean()

    select = search.propertySpecs.select()
    select.bedrooms()

    select = search.departures.select()
    select.date()
    
    # Set conditions for bookings
    where = search.details.where()
    where.isOwner().isFalse()
    where.enquirySource().isNotEqualTo('Direct')
    
    # Set conditions for flights
    where = search.arrivals.where()
    where.details().isNullEmptyOrFalse()
    where.flightNumber().isNullEmptyOrFalse()
    
    # Set conditions for emails if bookingId is not provided
    if not bookingId:
        where = search.emails.where()
        where.arrivalQuestionnaire().isEqualTo(emailSent)
        where.arrivalInformation().isFalse()
        
    return search.fetchall()


# Email sending functions
def _send_new_guest_four_weeks_email(
    booking: Booking, 
    html: bool=True, 
    bookingId: int = None
) -> GoogleMailMessage:
    """
    Prepare and send a four-week reminder email to a guest.
    
    Creates an email with arrival questionnaire information and 
    a link to complete the form.
    
    Args:
        booking: The booking object containing guest information.
        html: Whether to format the email as HTML.
        bookingId: Optional booking ID for tracking purposes.
        
    Returns:
        The sent email message object.
    """
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(
                                        topic='Arrival Questions',
                                        booking=booking)
    body: GoogleMailMessage.Body = message.body
    
    _opening(body)
    _introduction(body, booking)
    _explainer(body)    
    _note(body)    
    _please_click(body)
    _link(body, booking, html)
    _thank_you(body)
    
    if booking.arrival.isSoon: 
        _conclusion_now(body)
    else: 
        _conclusion_wait(body)
        
    _closing(body)
    
    send_guest_email(user, message, bookingId)
    return message


def _send_airbnb_messages(bookings: list[Booking]) -> None:
    """
    Send messages to Airbnb guests through the Airbnb messaging system.
    
    Args:
        bookings: List of Airbnb bookings to send messages to.
        
    Returns:
        None
    """
    airbnb: Browser = BrowseAirbnb().goTo().login().messages()
    
    for booking in bookings: 
        logbooking(booking, inline='Sending Airbnb message to:')

        airbnb.guest(booking.guest.name)
        airbnb.sendMessage(name='4 Weeks')
        airbnb.sendMessage(
            content=f'Secure Google Form Link: {_get_link(booking)}  ')

        booking.emails.arrivalQuestionnaire = updatedates.date()
        booking.emails.update()        

    airbnb.quit()
    return None


def _get_link(booking: Booking) -> str:
    """
    Get the Google Form link for a booking's arrival questionnaire.
    
    If the booking doesn't already have a form ID, creates a new form.
    
    Args:
        booking: The booking object to get or create a form for.
        
    Returns:
        The form responder URI that guests can use to complete the questionnaire.
    """
    formId: str = booking.forms.arrivalQuestionnaire
    if not formId:
        formId = set_guest_arrival_form(booking)

    responderUri: str = get_form_responder_uri(formId)
    return responderUri


# Email content functions
def _opening(body: GoogleMailMessage.Body) -> None:
    """
    Add opening paragraph to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I hope this finds you in good spirits and looking forward to your trip',
        'to Albufeira!'
    )


def _introduction(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add introduction paragraph with booking date to the email body.
    
    Args:
        body: The email body object to modify.
        booking: The booking object with arrival information.
        
    Returns:
        None
    """
    body.paragraph(
        'As we are closing in on your holiday start date',
        f'({booking.arrival.prettyDate}) this is our opportunity to touch base.',
        'To get things rolling and guarantee that all will be smooth and ready',
        'for your arrival, there are a few questions we kindly request you take',
        'a moment to answer.'
    )


def _explainer(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation about the form and available extras to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Below you will find a link to a secure Google Form. It asks about',
        ' plannedarrival times and gives you the chance to request optional',
        'extras such as children\'s cots and chairs, airport transfer services,',
        'food packs, additional cleaning, etc. All optional extras are paid for',
        'in cash on arrival.'
    )


def _note(body: GoogleMailMessage.Body) -> None:
    """
    Add important notes about check-in procedures to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'We are not a hotel and staff do not reside on location. All information',
        'you are able to share is highly appreciated. On an average day we deal',
        'with multiple ins and outs, so careful coordination is vital to ensure,',
        'rompt responses and prevent delays. Please note that there is a late',
        'check-in fee of €20.00 for flights landing 18:00 or later and all other',
        'arrivals after 20:00.'
    )


def _please_click(body: GoogleMailMessage.Body) -> None:
    """
    Add prompt to click the form link to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Please click or copy and paste into a new window:',
        bold=True
    )


def _link(
    body: GoogleMailMessage.Body, 
    booking: Booking, 
    html: bool = False) -> None:
    """
    Add the form link to the email body.
    
    Args:
        body: The email body object to modify.
        booking: The booking object containing the form ID.
        html: Whether to format the link as HTML with descriptive text.
        
    Returns:
        None
    """
    link = _get_link(booking)
    if not html or booking.details.enquirySource == 'Booking.com':
        body.link(link)
    else:
        body.link(
            link,
            f'ARRIVAL QUESTIONNAIRE FOR: {booking.guest.name}',
            bold=True
        )


def _thank_you(body: GoogleMailMessage.Body) -> None:
    """
    Add thank you note to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Once more, thank you for taking the time to complete this arrival',
        'questionnaire. When submitted, you should receive a copy of the',
        'responses in your email inbox.',
    )


def _conclusion_now(body: GoogleMailMessage.Body) -> None:
    """
    Add conclusion for guests arriving very soon to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Next, I will be sending full arrival information which will include',
        'everything you need to know for arrival day and beyond: property',
        'address, contact details, check-in instructions, etc.'
    )


def _conclusion_wait(body: GoogleMailMessage.Body) -> None:
    """
    Add conclusion for guests arriving later to the email body.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Two weeks before your arrival date, I will be sending full arrival',
        'information which will include property address, check-in instructions',
        'and other useful tips regarding your holiday.'
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
        'In the meantime, I remain available for questions. Not long to go!'
    )