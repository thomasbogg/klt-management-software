from datetime import date

from apis.google.mail.message import GoogleMailMessage
from correspondence.guest.arrival.registration.run import (
    get_guest_registration_attachment,
    new_guest_arrival_email,
    registration_link,
    sef_explanation,
    sef_request,
    sef_residents,
    send_guest_email,
    tax_explanation,
    tax_exemption,
    tax_request,
    tourist_tax_link
)
from correspondence.guest.functions import (
    new_guest_contact, 
    send_guest_whatsapp_message
)
from correspondence.owner.guest_registration.run import send_new_guest_registration_to_owner_email
from default.booking.booking import Booking
from default.booking.functions import (
    determine_tourist_tax,
    guest_has_stayed_before,
    logbooking
)
from default.database.database import Database
from default.database.functions import get_database
from default.dates import dates
from default.update.dates import updatedates as updateDates
from default.update.wrapper import update
from default.whatsapp.functions import login_to_whatsapp
from forms.functions import get_forms_bookings
from forms.registration.parser import PIMSGuestRegistrationParser
from PIMS.browser import BrowsePIMS
from utils import log, sublog, logdivider
from web.whatsapp import BrowseWhatsApp


#######################################################
# MAIN UPDATE FUNCTION
#######################################################

@update
def update_from_guest_registrations(
    start: date | None = None, 
    end: date | None = None, 
    bookingId: int | None = None) -> str:
    """
    Process guest registration forms and update booking information.
    
    This function checks for completed guest registration forms, extracts data
    from them, updates the database, and sends reminders to guests who haven't
    completed their forms.
    
    Args:
        start: Start date for bookings to check.
        end: End date for bookings to check.
        bookingId: Specific booking ID to check.
    
    Returns:
        A status message indicating the result of the operation.
    """
    if start is None and end is None: 
        start, end = updateDates.guest_registrations_dates()
    
    database = get_database()
    bookings = get_guest_registration_form_bookings(
                                                    database, 
                                                    start=start, 
                                                    end=end, 
                                                    bookingId=bookingId)
    if not bookings: 
        database.close()
        return 'GOT NO new guests to check for registrations' 
    
    browser = BrowsePIMS().goTo().login()
    parser = PIMSGuestRegistrationParser()
    whatsappPrompts = list()
    
    for booking in bookings:
        firstName = booking.guest.firstName
        lastName = booking.guest.lastName
        log(f'Looking at form for {firstName} {lastName}...')
        
        hasNif = bool(booking.guest.nifNumber)
        if not hasNif:
            parser.html = (
                            browser
                            .goTo(booking.forms.guestRegistration)
                            .frame(0)
                            .html
            )
            parser.firstName = firstName
            parser.lastName = lastName
            
            if not parser.hasInfo:
                browser.orderForms.unlockGuestRegistrationForm(booking.details.PIMSId)
                arrivalDate = booking.arrival.date
                
                if arrivalDate > dates.date():
                    sublog('Form is empty but arrival date is in the future. Skipping.')
                    continue
                
                if guest_has_stayed_before(booking): 
                    sublog('Form is empty but guest has stayed before. Skipping.')
                    booking.forms.guestRegistrationDone = True
                    booking.forms.update()
                    continue
                
                if booking.emails.paused: 
                    continue
                
                if dates.date() == dates.calculate(date=arrivalDate, days=1):
                    sublog('Form is empty will send WhatsApp prompt.')
                    whatsappPrompts.append(booking)
                    continue
                
                sublog('Form is empty will send Email prompt.')
                send_new_registration_reminder_email(booking)
                continue
        
        sublog('Form has answers...')
        if booking.property.ownerRegistersGuests:
            if not booking.emails.guestRegistrationFormToOwner:
                sublog('Owner registers their guest. Will send email.')
                send_new_guest_registration_to_owner_email(booking)
                booking.emails.guestRegistrationFormToOwner = True
        
        if not booking.guest.idCard and not hasNif:
            booking.guest.idCard = parser.passport
            booking.guest.nationality = parser.issuer
        
        booking.forms.guestRegistrationDone = True
        booking.update()
    
    browser.quit()
    
    if whatsappPrompts:
        send_whatsapp_prompts(whatsappPrompts)
    
    database.close()
    return 'Successfully parsed all guest registrations!'


#######################################################
# DATABASE FUNCTIONS
#######################################################

def get_guest_registration_form_bookings(
    database: Database | None = None, 
    start: date | None = None, 
    end: date | None = None, 
    bookingId: int | None = None
) -> list[Booking]:
    """
    Retrieve guest registration form links from the database based on specified criteria.
    
    Args:
        database: Database connection to use.
        start: Start date for bookings to retrieve.
        end: End date for bookings to retrieve.
        bookingId: Specific booking ID to retrieve.
        
    Returns:
        List of booking objects that require guest registration.
    """
    search = get_forms_bookings(database, start, end, bookingId)

    # Selections for booking details
    select = search.details.select()
    select.PIMSId()
    
    # Selections for guests
    select = search.guests.select()
    select.nifNumber()
    select.idCard()
    
    # Selections for properties
    select = search.properties.select()
    select.ownerRegistersGuests()
    select.weBook()
    select.alNumber()
    
    # Selections for owners
    select = search.propertyOwners.select()
    select.name()
    select.email()
    
    # Selections for forms
    select = search.forms.select()
    select.id()
    select.guestRegistration()
    select.PIMSuin()
    select.PIMSoid()
    
    # Selections for addresses
    select = search.propertyAddresses.select()
    select.location()
    
    # Selections for emails
    select = search.emails.select()
    select.id()
    select.guestRegistrationFormToOwner()
    select.paused()
    
    # Selections for extras
    select = search.extras.select()
    select.id()
    
    # Setting conditions
    where = search.details.where()
    where.isOwner().isFalse()
    
    if not bookingId:
        # Forms conditions
        where = search.forms.where()
        where.guestRegistrationDone().isNullEmptyOrFalse()

        where = search.emails.where()
        where.guestRegistrationForm().isTrue()

        # Guests conditions
        where = search.guests.where()
        where.nifNumber().isNullEmptyOrFalse()

        where = search.departures.where()
        where.date().isGreaterThan(dates.date())

    return search.fetchall()


#######################################################
# EMAIL FUNCTIONS
#######################################################

def send_new_registration_reminder_email(booking: Booking) -> None:
    """
    Send a reminder email to guests about completing their registration form.
    
    Args:
        booking: The booking to send the reminder for.
        
    Returns:
        None
    """
    topic = '(IMPORTANT) Guest Registration and Tourist Tax'
    user, message = new_guest_arrival_email(topic=topic, booking=booking)
    message.attachments = get_guest_registration_attachment()
    body = message.body
    opening(body)
    
    # GUEST REGISTRATION
    body.section('Legal Registration of Group')
    sef_explanation(body)
    sef_request(body)
    registration_link(body, booking)
    sef_residents(body)
    
    # TOURIST TAX PAYMENT
    body.section('Tourist Tax Payment')
    tax_explanation(body)
    if determine_tourist_tax(booking): 
        tax_request(body)
        tourist_tax_link(body, booking)
    else:
        tax_exemption(body)
    
    thank_you(body)
    send_guest_email(user, message)


def opening(body: GoogleMailMessage.Body) -> None:
    """
    Add an opening paragraph to the email.
    
    Args:
        body: The message body to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I hope you have settled into the accommodation and are',
        'enjoying your time in Albufeira. If there is anything',
        'we can do for you, please let me know.'
    )


def thank_you(body: GoogleMailMessage.Body) -> None:
    """
    Add a thank you paragraph to the email.
    
    Args:
        body: The message body to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Thank you very much for your understanding and patience.'
    )


#######################################################
# WHATSAPP FUNCTIONS
#######################################################

def send_whatsapp_prompts(bookings: list[Booking] = None, bookingId: int = None) -> str:
    """
    Send WhatsApp prompts to guests requesting registration form completion.
    
    Args:
        bookings: List of bookings to send WhatsApp messages for.
        
    Returns:
        A message indicating the result of the operation.
    """
    if not bookings:
        if not bookingId:
            return
        bookings = get_guest_registration_form_bookings(bookingId=bookingId)

    whatsapp: BrowseWhatsApp = login_to_whatsapp()
    logdivider()
    
    for booking in bookings:
        logbooking(booking, inline='Sending WhatsApp prompt to:')
        new_guest_contact(booking)
        
        content = [
            whatsapp_opening(booking),
            whatsapp_explanation(),
            whatsapp_form_link(booking),
            whatsapp_portuguese_residency(),
            whatsapp_thank_you(),
        ]
        sent = send_guest_whatsapp_message(whatsapp, booking, content)
    
        if not sent:
            logbooking(booking, inline=f'Failed to send WhatsApp prompt for:')

    whatsapp.quit()
    return 'Sent WhatsApp prompts for guest registration forms!'


def whatsapp_opening(booking: Booking) -> str:
    """
    Create a personalized WhatsApp opening message.
    
    Args:
        booking: The booking to create a message for.
        
    Returns:
        The formatted opening message.
    """
    return ' '.join([
        'My name is Thomas. I am one of the property managers at Algarve Beach',
        'Apartments. We hope that you are having a lovely time at',
        f'{booking.property.address.location}.'
    ])


def whatsapp_explanation() -> str:
    """
    Create a WhatsApp message explaining the registration requirement.
    
    Returns:
        The formatted explanation message.
    """
    return ' '.join([
        'We now need to get details to register your stay',
        'with the Portuguese government. Below is a secure link to the',
        'form that all guests must complete. Please attend to it as',
        'soon as possible.',
    ])


def whatsapp_form_link(booking: Booking) -> str:
    """
    Create a WhatsApp message with the registration form link.
    
    Args:
        booking: The booking to create a form link for.
        
    Returns:
        The form link message.
    """
    return booking.forms.guestRegistration


def whatsapp_portuguese_residency() -> str:
    """
    Create a WhatsApp message about Portuguese residency alternatives.
    
    Returns:
        The formatted Portuguese residency message.
    """
    return ' '.join([
        'NOTE: if you have *Portuguese residency*, we only require your Número de',
        'Identificação Fiscal. If this is your case, kindly reply below with the NIF',
        'and ignore the form.',
    ])


def whatsapp_thank_you() -> str:
    """
    Create a WhatsApp thank you message.
    
    Returns:
        The formatted thank you message.
    """
    return ' '.join([
        'Thank you very much in advance for your understanding and cooperation.',
        'If you have questions, I am available.',
    ])