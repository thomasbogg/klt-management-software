from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.dates import dates
from default.update.wrapper import pull_database
from forms.arrival.guest.run import update_from_guest_arrival_forms
from forms.arrival.owner.run import update_from_owner_arrival_forms
from interface.arrivaldeparture import update_arrival_departure
from interface.charges import update_charges
from interface.details import update_details
from interface.emails import (
    send_emails,
    update_emails
)
from interface.extras import update_extras
from interface.forms import update_forms
from interface.functions import (
    get_interface_booking,
    get_interface_bookings
)
from interface.guests import update_guests
from interface.manual import manually_fill_arrival_questionnaire
from interface.source import update_at_source
from interfaces.interface import Interface


@pull_database
def main() -> bool:
    """
    Main entry point for the KLT bookings management application.
    
    Sets up the interface and database connection, runs the application loop,
    and handles proper cleanup on exit.
    
    Returns:
        bool: Result of interface closure
    """
    interface = Interface(title='THIS IS THE GUI FOR KLT BOOKINGS MANAGMENT')
    keepRunning = True
    database = get_database()
    
    while keepRunning:
        keepRunning = run(interface, database)
    
    database.close()
    return interface.close()


def run(interface: Interface, database: Database) -> bool:
    """
    Run a single iteration of the booking update process.
    
    Args:
        interface: The application interface
        database: The database connection
    
    Returns:
        bool: Whether to continue running the application
    """
    sections = interface.subsections()
    databaseBooking = get_update_booking(sections, database)
    
    if not databaseBooking:
        return False
    
    updatedBooking = Booking()
    keepRunning = get_update_option(sections, database, databaseBooking, updatedBooking)
    
    return keepRunning


def get_update_booking(sections: Interface, database: Database) -> Booking | None:
    """
    Search for and retrieve a booking to update from the database.
    
    Args:
        sections: Interface subsection for UI elements
        database: The database connection
    
    Returns:
        Booking | None: The selected booking or None if search was cancelled
    """
    sections.section('FIRST, find the booking to update')
    search = sections.text('Type guest name, booking ID or property name')
    
    if search is None:
        return None
    
    try:
        integer = int(search)
        booking = get_interface_booking(database, bookingId=integer)
        return booking
    except:
        if dates.month() > 10:
            start = dates.date(month=10, day=1)
        elif dates.month() < 5:
            start = dates.date(year=dates.year(-1), month=10, day=1)
        else:
            start = dates.calculate(days=-30)
        
        end = dates.calculate(days=120)
        bookings = get_interface_bookings(
            database, 
            propertyName=search.upper(), 
            start=start, 
            end=end, 
            onlyValid=True
        )
    
    if not bookings:
        names = search.split()
        
        if len(names) < 2:
            firstName, lastName = None, names[0].capitalize()
        else:
            firstName, lastName = names[0].capitalize(), names[-1].capitalize()
        
        bookings = get_interface_bookings(
            database, 
            guestFirstName=firstName, 
            guestLastName=lastName
        )
    
    if not bookings:
        sections.log('ERROR: couldn\'t find any bookings for this search. Let\'s try again')
        return get_update_booking(sections, database)
    
    if len(bookings) == 1:
        return bookings[0]
    
    while True:
        sections.section('FOUND multiple bookings for this search. Choose one.')
        option = sections.option([booking.__repr__() for booking in bookings])
    
        if option is None:
            return None

        if option > len(bookings):
            sections.log('ERROR: Invalid option selected. Please try again.')
            continue

        return bookings[option - 1]


def get_update_option(
    sections: Interface,
    database: Database,
    databaseBooking: Booking, 
    updatedBooking: Booking
) -> bool:
    """
    Display and handle booking update options.
    
    Args:
        sections: Interface subsection for UI elements
        database: The database connection
        databaseBooking: The booking to update
        updatedBooking: A fresh booking object to receive updates
    
    Returns:
        bool: Whether to continue running the application
    """
    sections.section(f'GOT BOOKING: {databaseBooking.__repr__()}')
    
    option = sections.option([
        'See all details', 
        'Update Extras', 
        'Update Arrival/Departure details', 
        'Update Charges', 
        'Update Guest(s)',
        'Send Emails',
        'Update from Arrival Form',
        'Manually fill Arrival Form',
        'Update Forms',
        'Set Emails',
        'Update Details',
        'Update from Database Sources',
        'Work with another booking',
    ])
    
    subsection = sections.subsections()
    
    if option is None:
        return False
    elif option == 1:
        print(databaseBooking)
    elif option == 2:
        update_extras(subsection, databaseBooking, updatedBooking)
    elif option == 3:
        update_arrival_departure(subsection, databaseBooking, updatedBooking)
    elif option == 4:
        update_charges(subsection, databaseBooking)
    elif option == 5:
        update_guests(subsection, databaseBooking, updatedBooking)
    elif option == 6:
        send_emails(subsection, databaseBooking)
    elif option == 7:
        if databaseBooking.details.isOwner:
            update_from_owner_arrival_forms(bookingId=databaseBooking.details.id)
        else:
            update_from_guest_arrival_forms(bookingId=databaseBooking.details.id)
    elif option == 8:
        manually_fill_arrival_questionnaire(database, subsection, databaseBooking)
    elif option == 9:
        update_forms(subsection, databaseBooking)
    elif option == 10:
        update_emails(subsection, databaseBooking)
    elif option == 11:
        update_details(subsection, databaseBooking)
    elif option == 12:
        update_at_source(databaseBooking)
    elif option == 13:
        return True
    
    if option > 1:
        databaseBooking = get_interface_booking(database, databaseBooking.details.id)
   
    return get_update_option(sections, database, databaseBooking, updatedBooking)


if __name__ == '__main__':
    main()