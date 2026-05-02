from typing import Any

from dates import dates
from databases.table import Table
from default.booking.arrival import Arrival
from default.booking.booking import Booking
from default.booking.charges import Charges
from default.booking.departure import Departure
from default.booking.emails import Emails
from default.booking.extras import Extras
from default.booking.forms import Forms
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import (
    get_booking, 
    search_bookings,
    search_properties, 
    search_valid_bookings, 
)
from default.property.functions import update_properties_information_in_database
from default.update.wrapper import pull_database
from interfaces.interface import Interface
from utils import sublog


@pull_database
def main() -> None:
    """
    Main entry point for the KLT database management application.
    
    Sets up the interface and runs the database management options.
    """
    interface = Interface(title='THIS IS THE GUI FOR QUICK KLT DATABASE MANAGMENT')
    sections = interface.subsections()
    run(sections)


def run(sections: Interface) -> None:
    """
    Run the database management interface with various maintenance options.
    
    Provides options for database maintenance tasks such as updating property
    information, checking for data integrity issues, and examining booking overlaps
    
    Args:
        sections: Interface subsection for UI elements
    
    Returns:
        None when the user exits the application
    """
    sections.section('What do you want to do? HIT ENTER to exit.')
    option = sections.option(
        [
            'Update Properties Info in Database', 
            'Check for Duplicate Rows',
            'Check for Overlapping Bookings',
            'Check Unclosed Enquiries',
            'Check for Ghost bookingIds'
        ]
    )
    
    if option is None:
        return None
    
    if option == 1:
        sections.log('Updating properties information in database...')
        update_properties_information_in_database()
    elif option == 2:
        sections.log('Checking for duplicate rows...')
        _check_duplicate_rows(sections.subsections())
    elif option == 3:
        sections.log('Checking for overlapping bookings...')
        _check_overlapping_bookings(sections.subsections())
    elif option == 4:
        sections.log('Checking for unclosed enquiries...')
        _check_unclosed_enquiries(sections.subsections())
    elif option == 5:
        sections.log('Checking for ghost booking IDs...')
        _check_ghost_bookingIds(sections.subsections())

    return run(sections)


def _check_duplicate_rows(sections: Interface) -> None:
    """
    This function connects to the database, retrieves data from specified tables,
    and checks for duplicate rows based on the bookingId.
    """
    def __delete_or_ignore(
            sections: Interface, 
            unique: dict[int, Booking], 
            row: Table) -> None:
        """
        Placeholder function to handle duplicate rows.
        
        Args:
            row: The row to be handled (deleted or ignored).
        """
        sections.log(f'DUPLICATE FOUND')
        logbooking(_get_booking_by_id(row.bookingId), tabs=sections.indent + 1)
        sections.log(f'First found:')
        sections.sublog(unique[row.bookingId])
        sections.log(f'Second found:')
        sections.sublog(row)
      
        choice = sections.option(['Delete First', 'Delete Second', 'Ignore'])    
        if not choice:
            return

        if choice == 1:
            sections.log(f'Deleting first row...')
            unique[row.bookingId].delete()
            unique[row.bookingId] = row
        elif choice == 2:
            sections.log(f'Deleting second row...')
            row.delete()
        else:
            sections.log('Ignoring duplicate rows.')

    for attr, Object in (
        ('emails', Emails), 
        ('forms', Forms), 
        ('charges', Charges), 
        ('extras', Extras), 
        ('arrivals', Arrival), 
        ('departures', Departure)):
       
        sections.section(attr.upper())
        search = Database(loadObject=Object).connect()
        table: Table = getattr(search, attr)
        table.isPrimaryTable = True
        table.select().all()
        results = search.fetchall()
        unique: dict[int, Booking] = dict()

        for row in results:
            if row.bookingId not in unique:
                unique[row.bookingId] = row
            else:
                __delete_or_ignore(sections, unique, row)
        search.close()


def _check_overlapping_bookings(sections: Interface) -> None:
    """
    Check for overlapping bookings in the database.
    
    Args:
        sections: Interface subsection for logging results.
    
    Returns:
        None
    """
    def __cancel_or_ignore(
            sections: Interface, 
            previous: Booking, 
            current: Booking) -> None:
        """
        Placeholder function to handle overlapping bookings.

        Args:
            sections: Interface subsection for logging results.
            previous: The previous booking object.
            current: The current booking object.
        """
        sections.log(f'OVERLAP FOUND')
        logbooking(previous, inline='First:',  tabs=sections.indent + 1)
        logbooking(current, inline='Second:',  tabs=sections.indent + 1)
     
        choice = sections.option(['Cancel First', 'Cancel Second', 'Ignore'])
        if not choice:
            return
      
        if choice == 1:
            sections.log(f'Cancelling first booking...')
            previous.details.enquiryStatus = 'Booking cancelled'
            previous.update()
        elif choice == 2:
            sections.log(f'Cancelling second booking...')
            current.details.enquiryStatus = 'Booking cancelled'
            current.update()
        else:
  
            sections.log('Ignoring overlapping bookings.')
  
    search = search_properties()
    search.properties.where().weBook().isTrue()
    properties = search.fetchall()
    search.close()

    for property in properties: 
        search = search_valid_bookings(
                                    start=dates.date(), 
                                    end=dates.future(), 
                                    propertyName=property.shortName)
        search.details.select().all()
        search.guests.select().firstName().lastName()
        search.arrivals.select().date()
        search.departures.select().date()
        search.properties.select().shortName()
        results = search.fetchall()

        previousBooking = None
        for booking in results:
            if not previousBooking:
                previousBooking = booking
                continue
          
            if booking.arrival.date < previousBooking.departure.date:
                __cancel_or_ignore(sections, previousBooking, booking)
            previousBooking = booking

        search.close()


def _check_unclosed_enquiries(sections: Interface) -> None:
    """
    Check for unclosed enquiries in the database.
    
    Args:
        sections: Interface subsection for logging results.
    
    Returns:
        None
    """
    search = search_bookings()
    
    select = search.details.select()
    select.all()

    select = search.guests.select()
    select.firstName()
    select.lastName()

    select = search.arrivals.select()
    select.id()
    select.date()

    select = search.departures.select()
    select.id()
    select.date()

    select = search.forms.select()
    select.id()

    select = search.emails.select()
    select.id()

    select = search.charges.select()
    select.id()

    select = search.extras.select()
    select.id()

    select = search.properties.select()
    select.shortName()

    where = search.details.where()
    where.enquiryStatus().isIn(
        ('Open enquiry', 'Waiting for reply from guest'))
    where.enquiryDate().isLessThan(dates.calculate(days=-15))
    
    results = search.fetchall()

    if not results:
        sections.log('No unclosed enquiries found.')
        search.close()
        return

    sections.section('UNCLOSED ENQUIRIES')
    for booking in results:
        logbooking(booking, inline='Got:', tabs=sections.indent + 1)
        choice = sections.option(['Close Enquiry', 'Delete Enquiry', 'Ignore'])
        if not choice:
            continue
   
        if choice == 1:
            sections.log(f'Closing enquiry for booking...')
            booking.details.enquiryStatus = 'Booking cancelled'
            booking.update()
        elif choice == 2:
            sections.log(f'Deleting enquiry for booking...')
            booking.delete()

    search.close()


def _check_ghost_bookingIds(sections: Interface) -> None:
    """
    Check for ghost booking IDs in the database.
    
    Args:
        sections: Interface subsection for logging results.
    
    Returns:
        None
    """
    database = Database().connect()

    for table in ('arrivals', 'departures', 'forms', 'emails', 'charges', 'extras'):
        database.cursor.execute(f'SELECT bookingId FROM {table}')
        bookingIds = database.cursor.fetchall()
        for bookingId in bookingIds:
            database.cursor.execute(f'SELECT id FROM bookings WHERE id = {bookingId[0]}')
            result = database.cursor.fetchone()
            if not result:
                sections.log(f'GHOST BOOKING ID FOUND: {bookingId[0]} in table {table}')
                database.cursor.execute(f'DELETE FROM {table} WHERE bookingId = {bookingId[0]}')
                database.connection.commit()
                sections.log(f'GHOST BOOKING ID {bookingId[0]} DELETED FROM TABLE {table}')

    database.close()


def _get_booking_by_id(bookingId: int) -> Booking:
    """
    Retrieve a booking by its ID.
    
    Args:
        bookingId: The ID of the booking to retrieve.
    
    Returns:
        Booking object corresponding to the given ID.
    """
    search = get_booking(id=bookingId)

    select = search.details.select()
    select.enquirySource()
    select.enquiryStatus()

    select = search.guests.select()
    select.firstName()
    select.lastName()

    select = search.properties.select()
    select.shortName()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()

    result = search.fetchone()
    search.close()

    if result is None:
        raise ValueError(f'Booking with ID {bookingId} not found.')
    
    return result


if __name__ == '__main__':
    main()