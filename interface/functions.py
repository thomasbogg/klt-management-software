from datetime import date
from PIMS.browser import BrowsePIMS
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_booking,
    search_bookings, 
    set_valid_management_booking
)
from default.property.functions import determine_location
from interfaces.interface import Interface


# Database query functions
def get_interface_bookings(
    database: Database,
    guestFirstName: str | None = None,
    guestLastName: str | None = None,
    start: date | None = None,
    end: date | None = None,
    propertyName: str | None = None,
    bookingId: str | None = None,
    onlyValid: bool | None = None
) -> list[Booking]:
    """
    Get bookings with optional filtering criteria.
    
    Parameters:
        database: Database connection
        guestFirstName: Optional filter by guest first name
        guestLastName: Optional filter by guest last name
        start: Optional start date for arrival filter
        end: Optional end date for arrival filter
        propertyName: Optional property name or shortName
        bookingId: Optional specific booking ID
        onlyValid: If True, only return valid bookings
        
    Returns:
        List of Booking objects matching criteria
    """
    search = search_bookings(database, start, end)
    
    if onlyValid:
        set_valid_management_booking(search)
    
    set_search_selection(search)
    
    if bookingId:
        where = search.details.where()
        where.id().isEqualTo(bookingId)
    
    if guestFirstName:
        where = search.guests.where()
        where.firstName().isLike(guestFirstName)
    
    if guestLastName:
        where = search.guests.where()
        where.lastName().isLike(guestLastName)
    
    if propertyName:
        where = search.properties.where()
        where.shortName().isEqualTo(propertyName)
    
    return search.fetchall()


def get_interface_booking(
        database: Database, 
        bookingId: int = None) -> Booking | None:
    """
    Get a single booking by ID with all related data.
    
    Parameters:
        database: Database connection
        bookingId: The ID of the booking to retrieve
        phoneNumber: The phone number associated with the booking
    Returns:
        A Booking object or None if not found
    """
    search = get_booking(database, bookingId)
    set_search_selection(search)
    return search.fetchone()


def set_search_selection(search: Database) -> None:
    """
    Set the selection columns for a search object.
    
    Parameters:
        search: The search object to set selections for
    
    Returns:
        None
    """
    search.details.select().all()
    search.guests.select().all()
    search.extras.select().all()
    search.arrivals.select().all()
    search.departures.select().all()
    search.charges.select().all()
    search.emails.select().all()
    search.forms.select().all()
    
    select = search.properties.select()
    select.name()
    select.shortName()
    select.weClean()

    select = search.propertyOwners.select()
    select.name()
    select.email()

    select = search.propertyAddresses.select()
    select.location()


# Interface utility functions
def get_text(subsection: Interface, condition: str, current: str | None) -> str | None:
    """
    Get text input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        condition: Description of the field being changed
        current: Current value of the field
        
    Returns:
        New text value, current value if canceled, or None if cleared
    """
    value = subsection.text(f'Change {condition}? Current is {current}. Hit space bar once to clear.')

    if value is None:
        return current

    if value == ' ':
        return None

    return value


def get_float(subsection: Interface, charge: str, current: float, manual: bool) -> tuple[float, bool]:
    """
    Get float input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        charge: Description of the charge being changed
        current: Current value of the charge
        manual: Whether the charge is manually set
        
    Returns:
        Tuple of (new float value or current value if canceled, updated manual flag)
    """
    value = subsection.float(f'Set {charge} to...? Current is {current}')

    if value is None:
        return current, manual

    return value, True


def get_bool(subsection: Interface, condition: str, current: bool) -> bool:
    """
    Get boolean input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        condition: Description of the condition being changed
        current: Current boolean value
        
    Returns:
        New boolean value or current value if canceled
    """
    value = subsection.bool(f'Set {condition} to...? Current is {current}')

    if value is None:
        return current

    return value


def get_int(subsection: Interface, condition: str, current: int) -> int:
    """
    Get integer input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        condition: Description of the field being changed
        current: Current integer value
        
    Returns:
        New integer value or current value if canceled
    """
    value = subsection.integer(f'Change {condition} to...? Current is {current}')

    if value is None:
        return current

    return value


def get_date(subsection: Interface, condition: str, current: date) -> date:
    """
    Get date input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        condition: Description of the date being changed
        current: Current date value
        
    Returns:
        New date value or current value if canceled
    """
    value = subsection.date(f'Change {condition} to...? Current is {current}')

    if value is None:
        return current

    return value


def get_time(subsection: Interface, condition: str, current: str | None) -> str | None:
    """
    Get time input from user interface with current value as default.
    
    Parameters:
        subsection: Interface object for user interaction
        condition: Description of the time being changed
        current: Current time value
        
    Returns:
        New time value or current value if canceled
    """
    value = subsection.time(f'Change {condition} to...? Current is {current}')

    if value is None:
        return current

    return value


# PIMS-related functions
def should_update_PIMS(booking: Booking) -> bool:
    """
    Determine if a booking should be updated in PIMS system.
    
    Parameters:
        booking: Booking object to check
        
    Returns:
        True if booking should be updated in PIMS, False otherwise
    """
    if booking.details.enquirySource != 'Direct':
        return False
    
    if booking.details.isPlatform:
        return False
    
    if booking.details.isOwner:
        return False
    
    return True


def open_PIMS(booking: Booking) -> BrowsePIMS.orderForms:
    """
    Open PIMS browser interface for a specific booking.
    
    Parameters:
        booking: Booking object to open in PIMS
        
    Returns:
        BrowsePIMS object with order form open for the booking
    """
    browser = BrowsePIMS(visible=True).goTo().login()
    orderForms = browser.orderForms.goTo(booking.details.PIMSId)
    return orderForms


# Location-related functions
def get_location_criteria(sections: Interface) -> dict[str, str | None]:
    """
    Gets location criteria for selecting email recipients.
    
    Parameters:
        sections: Interface object for user interaction
        
    Returns:
        Dictionary containing location criteria
    """
    sections.section('Is it for all locations or specific?')
    options = (
        'All',
        'Quinta da Barracuda',
        'Clube do Monaco',
        'Parque da Corcovada',
    )
    location = sections.option(options)

    if location == 1:
        return determine_location(None)
    return determine_location(options[location - 1])