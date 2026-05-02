from default.booking.booking import Booking
from default.database.database import Database
from default.guest.guest import Guest
from default.updates.functions import update_to_database
from interface.functions import (
    get_bool,
    get_int,
    get_text,
    get_time,
)
from interfaces.interface import Interface


def manually_fill_arrival_questionnaire(database: Database, subsection: Interface, booking: Booking) -> None:
    """
    Manually fill the arrival questionnaire for a booking.
    
    Retrieves answers from the user interface and updates the booking object
    accordingly, including guest details, arrival/departure information, and extras.
    
    Parameters:
        database: Database connection
        subsection: Interface object for user interaction
        booking: Booking object to update with questionnaire answers
    
    Returns:
        None
    """
    isOwner = booking.details.isOwner
    bookingType = 'OWNER BOOKING' if isOwner else 'GUEST BOOKING'
    subsection.section(f'Manually fill arrival questionnaire for {bookingType}')
    
    # Owner booking details
    if isOwner:
        booking.details.adults = get_int(subsection, 'Adults', booking.details.adults)
        booking.details.children = get_int(subsection, 'Children', booking.details.children)
        booking.details.babies = get_int(subsection, 'Babies', booking.details.babies)

        booking.arrival.meetGreet = get_bool(subsection, 'Owner Meet & Greet', booking.arrival.meetGreet)
        booking.departure.clean = get_bool(subsection, 'Owner Clean', booking.departure.clean)

        forOwner = subsection.bool('Is this booking for the owner and/or their family (1 for YES, 0 for NO)? If not, we will create new guest details...')

    # Guest details
    if not isOwner or not forOwner:
        if isOwner and not forOwner:
            booking.guest = new_guest(database)
            booking.guest.firstName = get_text(subsection, 'First Name', booking.guest.firstName)
            booking.guest.lastName = get_text(subsection, 'Last Name', booking.guest.lastName)

        booking.guest.email = get_text(subsection, 'Email', booking.guest.email)
        booking.guest.phone = get_text(subsection, 'Phone', booking.guest.phone)

    # Arrival details
    booking.arrival.flightNumber = get_text(subsection, 'Arrival Flight Number', booking.arrival.flightNumber)
    if booking.arrival.flightNumber not in ('', None):
        booking.arrival.isFaro = get_bool(subsection, 'Is this flight to Faro?', booking.arrival.isFaro)
    booking.arrival.time = get_time(subsection, 'Arrival Time', booking.arrival.time)
    booking.arrival.details = get_text(subsection, '(Other) Arrival Details', booking.arrival.details)

    # Departure details
    booking.departure.flightNumber = get_text(subsection, 'Departure Flight Number', booking.departure.flightNumber)
    if booking.departure.flightNumber not in ('', None):
        booking.departure.isFaro = get_bool(subsection, 'Is this flight from Faro?', booking.departure.isFaro)
    booking.departure.time = get_time(subsection, 'Departure Time', booking.departure.time)
    booking.departure.details = get_text(subsection, '(Other) Departure Details', booking.departure.details)

    # Extras details
    booking.extras.airportTransfers = get_bool(subsection, 'Airport Transfers', booking.extras.airportTransfers)
    booking.extras.midStayClean = get_bool(subsection, 'Mid-Stay Clean', booking.extras.midStayClean)
    booking.extras.cot = get_int(subsection, 'Cot', booking.extras.cot)
    booking.extras.highChair = get_int(subsection, 'High Chair', booking.extras.highChair)
    booking.extras.welcomePack = get_bool(subsection, 'Welcome Pack', booking.extras.welcomePack)
    booking.extras.lateCheckout = get_bool(subsection, 'Late Check-out', booking.extras.lateCheckout)

    # Update the booking in the database
    booking.update()

    # Add notification to management team if needed 
    if booking.emails.management:
        update_to_database(booking, details='Arrival Form has been filled out')

    return None


def new_guest(database: Database) -> Guest:
    """
    Create a new guest object with default values.
    
    Parameters:
        database: Database connection to associate with the guest object
    
    Returns:
        A new Guest object with empty name and contact fields
    """
    guest = Guest(database)
    guest.firstName = ''
    guest.lastName = ''
    guest.email = ''
    guest.phone = ''
    return guest