from datetime import date
from os import getcwd, path

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.guest.arrival.functions import (
    get_guest_arrival_email_bookings,
    linen_care_1,
    linen_care_2,
    new_guest_arrival_email
)
from correspondence.guest.functions import send_guest_email
from correspondence.guest.arrival.functions import (
    code_of_conduct_explainer,
    get_code_of_conduct_attachment
)
from default.booking.booking import Booking
from default.booking.functions import determine_tourist_tax
from default.database.database import Database
from default.database.functions import get_database
from default.update.dates import updatedates
from default.update.wrapper import update
from PIMS.browser import BrowsePIMS


# Main API functions
@update
def send_guest_registration_emails(
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> str:
    """
    Send guest registration and tourist tax emails to bookings within a date range.
    
    Args:
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        emailSent: Whether to filter for bookings that already received emails
        bookingId: Optional specific booking ID to process
        
    Returns:
        str: Status message indicating success or no emails to send
    """
    if not bookingId and start is None and end is None: 
        start, end = updatedates.guest_registration_emails_dates() 
    
    database = get_database()
    bookings = get_guest_registration_bookings(database, start, end, emailSent, bookingId)
    
    if not bookings: 
        database.close()
        return 'NO new emails to send.'

    browser = BrowsePIMS().goTo().login()
    orderForms = browser.orderForms
    
    for booking in bookings:
        if not booking.guest.email: 
            continue
        send_new_guest_registration_email(booking, bookingId)
        
        # Update email status
        booking.emails.guestRegistrationForm = True
        booking.update()
        orderForms.unlockGuestRegistrationForm(booking.details.PIMSId)

    browser.quit()
    database.close()
    return 'All emails sent!'


def get_guest_registration_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    emailSent: bool = False,
    bookingId: int = None
) -> list[Booking]:
    """
    Retrieve bookings that need guest registration emails.
    
    Args:
        database: Database connection
        start: Start date for filtering arrivals
        end: End date for filtering arrivals
        emailSent: Whether registration email has been sent
        bookingId: Optional specific booking ID to retrieve
        
    Returns:
        list[Booking]: Bookings that need guest registration emails
    """
    # Initialize the search using the higher-level function
    search = get_guest_arrival_email_bookings(
        database, start=start, end=end, bookingId=bookingId
    )
    
    # Select details from the bookings table
    select = search.details.select()
    select.enquiryDate()
    select.PIMSId()
    select.adults()
    select.children()
    select.babies()
    select.enquirySource()
    
    # Select guest details 
    select = search.guests.select()
    select.nifNumber()
    
    # Select arrival and departure dates
    select = search.departures.select()
    select.date()
    
    # Select forms details
    select = search.forms.select()
    select.guestRegistration()
    select.PIMSuin()
    select.PIMSoid()
    
    # Select property details
    select = search.properties.select()
    select.alNumber()
    select.weBook()

    # Select property address details
    select = search.propertyAddresses.select()
    select.location()
    
    # Apply conditions
    where = search.details.where()
    where.isOwner().isFalse()
    
    where = search.properties.where()
    where.weBook().isTrue()
    
    # Apply email conditions if not filtering by bookingId
    if not bookingId:
        where = search.emails.where()
        where.guestRegistrationForm().isEqualTo(emailSent)
        where.arrivalInformation().isTrue()
    
    return search.fetchall()


def send_new_guest_registration_email(
    booking: Booking,
    bookingId: int = None
) -> None:
    """
    Create and send guest registration email with tourist tax information.
    
    Creates an email with registration links, tourist tax information,
    and house rules for the guest's stay.
    
    Args:
        booking: The booking object containing guest information
        bookingId: Optional booking ID for tracking purposes
        
    Returns:
        None
    """
    user: GoogleMailMessages
    message: GoogleMailMessage
    user, message = new_guest_arrival_email(
        topic='Guest Registration and Tourist Tax Payment', 
        booking=booking
    )
    body: GoogleMailMessage.Body = message.body

    # Opening section
    _opening(body, booking)
    body.separation()
    
    if booking.details.isPlatform:
        _opening_2(body)
        _opening_3(body)
    else:
        _explanation(body)
        
    # Guest registration section
    body.section('Legal Registration of Group')
    if not booking.guest.nifNumber:
        message.attachments = get_guest_registration_attachment()
        sef_explanation(body)
        sef_request(body)
        registration_link(body, booking)
        sef_residents(body)
    else:
        sef_exemption(body)

    # Tourist tax payment section
    body.section('Tourist Tax Payment')
    tax_explanation(body)
    if determine_tourist_tax(booking): 
        tax_request(body)
        tourist_tax_link(body, booking)
    else:
        tax_exemption(body)

    if booking.details.isPlatform:
        # Make-up advice section
        body.section('Towel and Linen Care')
        linen_care_1(body)    
        linen_care_2(body)    
        
        # House rules section
        body.section('House Rules')        
        _house_rules_intro(body, booking)        
        _house_rules_1(body)        
        _house_rules_2(body)
        _house_rules_3(body)
        _house_rules_4(body)

        # Albufeira code of conduct section
        body.section('Albufeira\'s Tourist Code of Conduct')
        message.attachments = get_code_of_conduct_attachment()
        code_of_conduct_explainer(body)
    
    body.separation()
    _thank_you(body)
    
    send_guest_email(user, message, bookingId)
    return None


# Helper functions
def get_guest_registration_attachment() -> str:
    """
    Get the full path to the guest registration explainer PDF.
    
    Returns:
        str: Full path to the PDF attachment
    """
    abs = getcwd()
    filedir = 'correspondence/guest/arrival/registration'
    filename = 'Mandatory_Guest_Registration_Explainer.pdf'
    attachmentPath = path.join(abs, filedir, filename)
    if not path.exists(attachmentPath):
        raise FileNotFoundError(f'Attachment not found: {attachmentPath}')
    return attachmentPath


# Email content sections
def _opening(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add opening paragraph welcoming the guest.
    
    Args:
        body: The email body object to modify
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        'You will shortly be kicking-off your holiday in Albufeira!',
        f'We are so pleased that you have chosen to stay at {booking.property.name}.'
    )


def _explanation(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph explaining the email's purpose.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'This email is broken down into 2 parts. Both require your utmost attention.',
        'First, we will discuss the mandatory Guest Registration Form and then the',
        'mandatory Tourist Tax Payment.'
    )


def sef_explanation(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation about legal registration requirements.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'For legal reasons to do with the Serviço de Estrangeiros e Fronteiras',
        '(the Portuguese border enforcement agency), guests are required to fill',
        'out a form indicating passport numbers, place of birth, residence, and',
        'other similar details. Attached is a brief explainer with the relevant',
        'laws that compel this process.'
    )


def sef_exemption(body: GoogleMailMessage.Body) -> None:
    """
    Add exemption for legal registration requirements.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'For legal reasons to do with the Serviço de Estrangeiros e Fronteiras',
        '(the Portuguese border enforcement agency), guests are normally required to fill',
        'out a form indicating passport numbers, place of birth, residence, and',
        'other similar details. However, as you already have a NIF number on record'
        'with us, you are exempt from providing any further details.'
    )


def sef_residents(body: GoogleMailMessage.Body) -> None:
    """
    Add information for Portuguese residents.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'For <u>guests who have Resident status in Portugal</u>, we only require',
        'a Número de identificação Fiscal (NIF). If this is your case, please',
        'disregard the form above and simply reply to this email with your NIF',
        'number.'
    )


def sef_request(body: GoogleMailMessage.Body) -> None:
    """
    Add request to fill out registration form.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Please click the link below to open the form and fill out all required',
        'details:'
    )


def registration_link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add registration form link to the email.
    
    Args:
        body: The email body object to modify
        booking: The booking with guest information
        
    Returns:
        None
    """
    body.link(
        booking.forms.guestRegistration, 
        f'Guest Registration for {booking.guest.fullName}'
    )


def tax_explanation(body: GoogleMailMessage.Body) -> None:
    """
    Add explanation about tourist tax requirements.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'All guests staying nights in Albufeira between April and October who',
        'are over the age of 12 are subject to a tourist tax payment of €2 per',
        'night up to a maximum of 7 nights.'
    )


def tax_request(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions for paying tourist tax.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Please follow the link provided below to make this payment. It will ask',
        'you to enter your check-in and check-out dates as well as the number of',
        'people in your group. If you arrive before April, please only enter the',
        'nights stayed from the 1st April onwards; likewise, if departing after',
        'October only register the nights stayed up to the 31st October.'
    )


def tourist_tax_link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add tourist tax payment link to the email.
    
    Args:
        body: The email body object to modify
        booking: The booking with property information
        
    Returns:
        None
    """
    body.link(
        f'https://tt.360city.pt/?id=AL-{booking.property.alNumber}',
        f'Tourist Tax Payment for {booking.guest.fullName}'
    )


def tax_exemption(body: GoogleMailMessage.Body) -> None:
    """
    Add information about tax exemptions.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'However, your booking is exempt from payment on this occasion. But',
        'please be aware that future bookings will likely be subject to payment.'
    )


def _thank_you(body: GoogleMailMessage.Body) -> None:
    """
    Add closing thank you paragraph.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Thank you very much for your understanding and patience. We really',
        'look forward to welcoming you in a few days!'
    )


def _opening_2(body: GoogleMailMessage.Body) -> None:
    """
    Add additional opening paragraph for platform bookings.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'In this email, I would like to take a moment to discuss some important',
        'details regarding 1) mandatory Guest Registration, 2) mandatory Tourist',
        'Tax payment, 3) towel and linen care, 4) the property, as well 5)',
        'Albufeira\'s Tourist Code of Conduct.'
    )


def _opening_3(body: GoogleMailMessage.Body) -> None:
    """
    Add third opening paragraph for platform bookings.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'We really appreciate your attention to these matters. This is a process',
        'we go through with every guest and should take no more than 5 minutes.'
    )


def _house_rules_intro(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add introduction to house rules.
    
    Args:
        body: The email body object to modify
        booking: The booking with property information
        
    Returns:
        None
    """
    body.paragraph(
        f'{booking.property.address.location} is a prestigious property with',
        'many apartments which accommodate both temporary and full-time residents.',
        'It is a place of peace and respect that has gained its reputation through',
        'dedicated management and care. When at the property, guests are expected',
        'to treat the living space and the common areas as if in their own home',
        'and leave everything as tidy as they found it. In addition to this,',
        'there are some essential rules that must be followed at all times:'
    )


def _house_rules_1(body: GoogleMailMessage.Body) -> None:
    """
    Add first house rule about quiet hours.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        '- Quiet hours are in place between 22:00 and 08:00.'
    )


def _house_rules_2(body: GoogleMailMessage.Body) -> None:
    """
    Add second house rule about hanging items.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        '- It is not permitted to shake or hang towels, rugs or clothes on',
        'balconies, terraces and windows.'
    )


def _house_rules_3(body: GoogleMailMessage.Body) -> None:
    """
    Add third house rule about pool usage.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        '- Pool opening hours are between 09:00 and 21:00, and glass objects and',
        'ball games are not permitted in the vicinity.'
    )


def _house_rules_4(body: GoogleMailMessage.Body) -> None:
    """
    Add fourth house rule about pool usage.

    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        '- Sun beds cannot be reserved with towels or personal items. If the beds',
        'are left unattended for more than 10 minutes, other guests have the right',
        'to remove the items and use the beds.'
    )