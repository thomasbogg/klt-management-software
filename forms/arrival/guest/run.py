from datetime import date

from correspondence.guest.arrival.four_weeks.run import send_guest_four_weeks_emails
from correspondence.guest.functions import (
    new_guest_contact, 
    send_guest_whatsapp_message
)
from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import get_database
from default.dates import dates
from default.google.drive.functions import get_klt_management_directory_on_drive
from default.google.forms.functions import get_form_responder_uri, get_form
from default.update.dates import updatedates as updateDates
from default.update.wrapper import update
from default.updates.functions import update_to_database
from default.whatsapp.functions import login_to_whatsapp
from forms.arrival.functions import (
    get_arrival_form_booking,
    update_from_arrival_method_section, 
    update_from_extras_section
)
from forms.arrival.guest.functions import (
    get_form_responses, 
    update_from_guest_details_section
)
from forms.arrival.guest.responses import GuestArrivalFormResponses
from forms.functions import get_forms_bookings
from utils import log, logdivider, sublog
from web.whatsapp import BrowseWhatsApp



@update
def update_from_guest_arrival_forms(
        start: date | None = None,
        end: date | None = None,
        bookingId: int | None = None,
) -> str:
    """
    Updates information from guest arrival forms.
    
    Args:
        start: The start date for filtering arrival forms.
        end: The end date for filtering arrival forms.
        bookingId: Optional specific booking ID to process.
        
    Returns:
        A message indicating the result of the operation.
    """
    if start is None and end is None: 
        start, end = updateDates.arrival_forms_dates()
    
    database: Database = get_database()
    bookings: list[Booking] = get_arrival_form_bookings(database, start, end, bookingId)
    
    if not bookings: 
        database.close()
        return 'Found no arrival forms to look at.'
    
    whatsappPrompts: list[Booking] = list()
    
    for booking in bookings:
        name: str = booking.guest.fullName
        date: str = booking.arrival.prettyDate
        log(f'Looking at form for guest {name} arriving {date}')
       
        formId: str = booking.forms.arrivalQuestionnaire
        responses: GuestArrivalFormResponses = get_form_responses(formId)
        if not responses: 
            form = get_form(formId)
            if not form.isPublished:
                sublog(f'Form {formId} is not published yet. Publishing now.')
                form.publish()
            check_new_prompt(booking, whatsappPrompts)
            continue
        
        update_from_guest_details_section(booking, responses)
        update_from_arrival_method_section(booking, responses)
        update_from_extras_section(booking, responses)

        if not booking.emails.arrivalInformation and booking.emails.management:
            update_to_database(
                booking,
                details='UPDATED BOOKING:Guest has filled out arrival form'
            )
        booking.update()

    if whatsappPrompts:
        send_whatsapp_prompts(whatsappPrompts)
 
    database.close()
    return 'All arrival forms have been processed!'


def get_arrival_form_bookings(
        database: Database,
        start: date | None = None,
        end: date | None = None,
        bookingId: int | None = None,
) -> list[Booking]:
    """
    Retrieves arrival form bookings with specified conditions.

    Args:
        database: The database connection object.
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.
        bookingId: The specific booking ID to filter by.

    Returns:
        A list of Booking objects that match the criteria.
    """
    if bookingId:
        start, end = None, None
    search = get_forms_bookings(database, start, end, bookingId)
    
    select = search.details.select()
    select.enquirySource()
    select.platformId()
    
    select = search.forms.select()
    select.arrivalQuestionnaire()
    
    select = search.extras.select()
    select.id()

    select = search.emails.select()
    select.management()
    select.arrivalInformation()

    select = search.properties.select()
    select.weClean()

    select = search.propertySpecs.select()
    select.bedrooms()
    
    select = search.propertyAddresses.select()
    select.location()

    select = search.forms.select()
    select.arrivalQuestionnaire()

    select = search.emails.select()
    select.id()
    select.arrivalQuestionnaire()

    if not bookingId:
        where = search.details.where()
        where.isOwner().isFalse()
        
        where = search.arrivals.where()
        where.flightNumber().isNullEmptyOrFalse()
        where.details().isNullEmptyOrFalse()
    
    where = search.emails.where()
    where.arrivalQuestionnaire().isNotNullEmptyOrFalse()
    
    return search.fetchall()


def check_new_prompt(booking: Booking, whatsappPrompts: list[Booking]) -> None:
    """
    Check if a new WhatsApp prompt should be sent to the guest.
    
    Args:
        booking: The booking object for the guest.
        whatsappPrompts: List to store bookings that need a WhatsApp prompt.
    """
    
    if booking.arrival.date in updateDates.guestPromptDates(): 
        whatsappPrompts.append(booking)
    elif booking.arrival.date <= dates.calculate(days=3):
        whatsappPrompts.append(booking)
    elif booking.arrival.date <= updateDates.calculate(days=14):
        if not booking.guest.email: 
            return None
        
        lastSent: date = booking.emails.arrivalQuestionnaire
        if (
            not lastSent or
            not isinstance(lastSent, date) or
            updateDates.date() >= dates.calculate(date=lastSent, days=3)
        ): 
            send_guest_four_weeks_emails(bookingId=booking.id)
    
    return None


def send_whatsapp_prompts(bookings: list[Booking] = None, bookingId: int = None) -> str:
    """
    Sends WhatsApp prompts to guests to complete arrival forms.
    
    Args:
        bookings: List of bookings for which to send WhatsApp prompts.
        
    Returns:
        A message indicating the result of the operation.
    """
    whatsapp: BrowseWhatsApp = login_to_whatsapp()

    logdivider()

    if not bookings:
        if not bookingId:
            return 
        bookings = get_arrival_form_bookings(database=None, bookingId=bookingId)
    
    for booking in bookings:
        logbooking(booking, inline='Sending WhatsApp prompt to:')
        new_guest_contact(booking)
        
        content = [
            opening(booking),
            security_check(booking),
            explanation(booking),
            form_explanation(),
            form_link(booking),
            conclusion(),
            thank_you(),
        ]
        sent = send_guest_whatsapp_message(whatsapp, booking, content)
    
        if not sent:
            sublog(f'Failed to send WhatsApp prompt for booking ID: {booking.id}')
        else:
            booking.emails.arrivalQuestionnaire = dates.date()
            booking.emails.update()

    whatsapp.quit()
    return 'Sent WhatsApp prompts for arrival forms!'


def join(func):
    """
    Decorator that joins the strings in a list returned by a function.
    
    Args:
        func: The function to wrap.
        
    Returns:
        Wrapped function that returns a joined string.
    """
    def wrapper(*args) -> str:
        return ' '.join(func(*args))
    return wrapper


@join
def opening(booking: Booking) -> list[str]:
    """
    Creates an opening message for WhatsApp communication.
    
    Args:
        booking: The booking information for the guest.
        
    Returns:
        A list of strings to be joined into an opening message.
    """
    return [
        'My name is Thomas. I am one of the property managers at Algarve Beach',
        'Apartments.',
        f'We are expecting you at {booking.property.address.location} on',
        f'{booking.arrival.prettyDate}.'
    ]


@join
def security_check(booking: Booking) -> list[str]:
    """
    Creates a security verification message for WhatsApp.
    
    Args:
        booking: The booking information for the guest.
        
    Returns:
        A list of strings to be joined into a security check message.
    """
    return [
        'First, please check my phone number (+351 935 769 935)',
        'against the details on',
        f'{booking.details.enquirySource}. Please also',
        'confirm that this is the',
        f'reservation number: {booking.details.platformIdStripped}.'
    ]


@join
def explanation(booking: Booking) -> list[str]:
    """
    Creates an explanation message about contacting the guest.
    
    Args:
        booking: The booking information for the guest.
        
    Returns:
        A list of strings to be joined into an explanation message.
    """
    return [
        'I am contacting you because we have not been able to get through',
        f'via {booking.details.enquirySource}.',
        'As we are approaching the start of your holiday, we would like to',
        'send you arrival instructions.'
    ]


@join
def form_explanation() -> list[str]:
    """
    Creates an explanation message about the arrival form.
    
    Returns:
        A list of strings to be joined into a form explanation message.
    """
    return [
        'However, to plan the check-in day properly, we kindly ask that you',
        'fill out a short arrival form. It should only take 2 minutes.'
    ]


@join
def form_link(booking: Booking) -> list[str]:
    """
    Creates a message containing the arrival form link.
    
    Args:
        booking: The booking information for the guest.
        
    Returns:
        A list of strings to be joined into a form link message.
    """
    return [
        'Here is the link to the form:',
        f'{get_form_responder_uri(booking.forms.arrivalQuestionnaire)}'
    ]


@join
def conclusion() -> list[str]:
    """
    Creates a concluding message about arrival preparation.
    
    Returns:
        A list of strings to be joined into a conclusion message.
    """
    return [
        'We do not want your arrival in Albufeira to be stressful, so',
        'please do take a moment with this.'
    ]


@join
def thank_you() -> list[str]:
    """
    Creates a thank you message.
    
    Returns:
        A list of strings to be joined into a thank you message.
    """
    return [
        'Thank you very much.'
    ]


@update
def delete_old_guest_arrival_forms(
        end: date | None = None,
) -> str:
    """
    Deletes old guest arrival forms from Google Drive.
    
    Args:
        end: The end date for filtering forms to delete. If None, uses default dates.
        
    Returns:
        A message indicating the result of the operation.
    """
    if end is None: 
        end = updateDates.delete_old_arrival_forms_date()

    drivePath = 'Forms/Guest Arrival Preparation Questionnaire'
    folder = get_klt_management_directory_on_drive(drivePath)
    files = folder.files
    database: Database = get_database()

    for file in files:
        if file.name == 'Empty Google Form':
            continue
        booking = get_arrival_form_booking(database, file.id)
        if not booking:
            log(booking, f"No booking found for form {file.name} with ID {file.id}")
            continue
        if booking.departure.date < end:
            logbooking(booking, 'Deleting arrival form for:')
            file.delete()
    
    database.close()
    return 'Successfully deleted old forms!'