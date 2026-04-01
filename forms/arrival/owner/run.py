import datetime

from correspondence.owner.four_weeks.run import send_owner_four_weeks_emails
from default.booking.functions import logbooking
from correspondence.self.functions import new_email_to_self
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.drive.functions import get_klt_management_directory_on_drive
from default.update.dates import updatedates
from forms.arrival.functions import (
    get_arrival_form_booking,
    update_from_arrival_method_section, 
    update_from_extras_section
)
from forms.arrival.owner.functions import (
    get_form_responses, 
    set_owner_arrival_form,
    update_from_guest_details_section, 
    update_from_booking_details_section,
    update_from_owner_comments_section
)
from forms.functions import get_forms_bookings
from utils import log, logdivider
from default.update.wrapper import update
from default.updates.functions import update_to_database


@update
def update_from_owner_arrival_forms(
        start: datetime.date = None, 
        end: datetime.date = None, 
        bookingId: int = None) -> str:
    """
    Update the database with information from owner arrival forms.
    This function retrieves owner arrival forms, processes them, and updates
    the database with the relevant information.

    Args:
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.
        bookingId: The specific booking ID to filter by.

    Returns:
        A message indicating the completion of the update process.
    """
    if start is None and end is None and bookingId is None: 
        start, end = updatedates.arrival_forms_dates()

    database = get_database()
    bookings = get_owner_arrival_form_bookings(database, start, end, bookingId)
    
    if not bookings: 
        database.close()
        return 'Found no arrival forms to look at.'
    
    commentsForEmail = list()
    
    for booking in bookings:
        log(
            f'Looking at form for {booking.property.name} ' \
            f'arriving {booking.arrival.prettyDate}'
        )

        if not booking.forms.arrivalQuestionnaire:
            set_owner_arrival_form(booking)
            
        responses = get_form_responses(booking.forms.arrivalQuestionnaire)
        if not responses:
            if booking.arrival.date in updatedates.guestPromptDates(): 
                send_owner_four_weeks_emails(bookingId=booking.id)
            continue    
        
        ### ADD ARRIVAL DATE AND CHECK UPDATES HERE
        if booking.emails.management:
            update_to_database(
                            booking, 
                            details='UPDATED BOOKING:Owner has filled out arrival form')

        update_from_booking_details_section(booking, responses)
        if not responses.selfBooking:
            update_from_guest_details_section(database, booking, responses)
        update_from_arrival_method_section(booking, responses)
        update_from_extras_section(booking, responses)
        update_from_owner_comments_section(booking, responses, selfEmail=commentsForEmail)

        booking.update()
    
    if commentsForEmail:
        logdivider()
        send_new_email_to_self_for_owner_form_comments(commentsForEmail)
    
    database.close()
    return 'All owner arrival forms have been processed!'


def get_owner_arrival_form_bookings(
        database: Database, 
        start: datetime.date = None, 
        end: datetime.date = None, 
        bookingId: int = None) -> list[Booking]:
    """
    Retrieves owner arrival form bookings with specified conditions.

    Args:
        database: The database connection object.
        start: The start date for filtering arrivals.
        end: The end date for filtering arrivals.
        bookingId: The specific booking ID to filter by.

    Returns:
        A list of Booking objects that match the criteria.
    """
    # Initialize search object from database
    search = get_forms_bookings(database, start, end, bookingId)
    
    # Select details from the bookings table
    select = search.details.select()
    select.enquirySource()
    
    # Select owner details
    select = search.propertyOwners.select()
    select.name()
    select.email()

    # Select property details
    select = search.properties.select()
    select.weClean()

    # Select property specs
    select = search.propertySpecs.select()
    select.bedrooms()
    
    # Select form details
    select = search.forms.select()
    select.arrivalQuestionnaire()

    select = search.emails.select()
    select.management()

    # Apply conditions
    where = search.details.where()
    where.isOwner().isTrue()
    
    # Apply booking ID condition if provided
    if not bookingId:
        where = search.arrivals.where()
        where.flightNumber().isNullEmptyOrFalse()
        where.details().isNullEmptyOrFalse()
    
    # Apply email conditions
    where = search.emails.where()
    where.arrivalQuestionnaire().isNotNullEmptyOrFalse()
    
    return search.fetchall()


def send_new_email_to_self_for_owner_form_comments(
        comments: list[tuple[Booking, str]]) -> None:
    """
    Sends an email to self with new owner comments on arrival forms.

    Args:
        comments: A list of tuples containing Booking objects and their associated comments.
    """
    user, message = new_email_to_self(subject='Owner Comments on Arrival Forms')
    body = message.body
    body.paragraph('There are new owner comments on Arrival Forms:')
    
    count = 0
    for booking, comment in comments:
        count += 1
        body.paragraph(f'{count}) {booking.__repr__()}')
        body.paragraph(f'Comment: {comment}')
    
    message.send()


@update
def delete_old_owner_arrival_forms(
        end: datetime.date | None = None,
) -> str:
    """
    Deletes old owner arrival forms from Google Drive.
    
    Args:
        start: The start date for filtering forms to delete. If None, uses default dates.
        end: The end date for filtering forms to delete. If None, uses default dates.
        
    Returns:
        A message indicating the result of the operation.
    """
    if end is None: 
        end = updatedates.delete_old_arrival_forms_date()

    folder = get_klt_management_directory_on_drive('Forms/Owner Arrival Preparation Questionnaire')
    files = folder.files
    database: Database = get_database()

    for file in files:
        if file.name == 'Empty Google Form':
            continue
        booking = get_arrival_form_booking(database, file.id)
        if not booking:
            log(f"No booking found for form {file.name} with ID {file.id}")
            continue
        if booking.departure.date < end:
            logbooking(booking, 'Deleting arrival form for:')
            file.delete()

    return 'Successfully deleted old forms!'