from datetime import date
import regex as re

from correspondence.self.functions import new_bookings_email_to_self
from default.booking.booking import Booking
from default.booking.functions import logbooking
from default.database.database import Database
from default.database.functions import (
    get_booking,
    get_database,
    search_valid_bookings
)
from default.update.dates import updatedates
from default.update.wrapper import update
from PIMS.browser import BrowsePIMS


@update
def update_PIMS_platform_bookings(start: date = None, end: date = None, 
                                 visible: bool = False) -> str:
    """
    Update platform booking details in PIMS with information from the database.
    
    Synchronizes platform bookings in PIMS by updating names, booking details,
    and linking database records with PIMS records. Identifies bookings with
    missing platform IDs and reports them via email.
    
    Parameters:
        start: Start date for filtering bookings, defaults to platform update dates
        end: End date for filtering bookings, defaults to platform update dates
        visible: Whether to show the browser window during execution
    
    Returns:
        Success message confirming the update
    """
    if start is None and end is None: 
        start, end = updatedates.PIMS_platform_update_dates()
    
    browser = BrowsePIMS(visible).goTo().login()
    reservationsList = browser.reservations.goTo()
    reservations = get_reservations(reservationsList, start, end).list
    orderForms = browser.orderForms
    noPlatId = []
    database = get_database()

    for reservation in reservations:
        if not guest_name_is_generic(reservation['guest']): 
            continue
      
        pimsId = reservation['orderId']
        orderForms.goTo(pimsId)
      
        booking = get_PIMS_booking(database, pimsId)
        if booking: 
            if not booking.details.platformId:
                if not is_platform_owner_booking(booking):
                    noPlatId.append(booking)
                    continue
        else:
            arrivalDate = reservation['arrival']
            departureDate = reservation['departure']
            propertyName = orderForms.propertyName
            booking = get_no_platId_booking(
                database, arrivalDate, departureDate, propertyName)
            if not booking: 
                noPlatId.append(set_dummy_booking(reservation, orderForms))
                continue
            booking.details.PIMSId = pimsId
            booking.details.update()

        name = get_name_for_PIMS(booking)
        logbooking(booking, inline=f'Updating @ PIMS:')
        set_order_form_fields(orderForms, booking, name)
    
    browser.quit()
    database.close()
    
    if noPlatId: 
        new_bookings_email_to_self(
            bookings=noPlatId, 
            subject='Missing Platform or PIMS IDs for PIMS Ical Import Bookings')
    return 'All bookings updated successfully'


# PIMS interaction functions
def get_reservations(reservations: BrowsePIMS.ReservationsList, start: date, 
                    end: date) -> BrowsePIMS.ReservationsList:
    """
    Configure search parameters and retrieve reservations from PIMS.
    
    Parameters:
        reservations: PIMS reservations list interface
        start: Start date for filtering bookings
        end: End date for filtering bookings
    
    Returns:
        Reservations list object with search results
    """
    reservations.propertyName = 'All Properties'
    reservations.start = start
    reservations.end = end
    reservations.resultsType = 'All active bookings only'
    reservations.updatedSince = updatedates.firstOfMonth(-1)
    reservations.sortBy = 'start_date'
    reservations.iCalOnly = True
    reservations.onlyOwner = False
    reservations.noOwner = False
    reservations.update()
    return reservations


def set_order_form_fields(orderForms: BrowsePIMS.OrderForms, booking: Booking, 
                         name: str) -> None:
    """
    Update PIMS order form fields with booking information.
    
    Parameters:
        orderForms: PIMS order forms interface
        booking: Booking object with data to update
        name: Guest name to display in PIMS
    
    Returns:
        None
    """
    if is_platform_owner_booking(booking): 
        orderForms.ownerBooking = True
    else: 
        orderForms.basicRental = booking.charges.basicRental
        orderForms.adminFee = 0
        orderForms.currency = booking.charges.currency
        orderForms.adults = booking.details.adults
        orderForms.children = booking.details.children
        orderForms.babies = booking.details.babies
    orderForms.lastName = name
    orderForms.update()


# Booking data functions
def set_dummy_booking(reservation: dict, orderForms: BrowsePIMS.OrderForms) -> Booking:
    """
    Create a temporary booking object for reservations without database records.
    
    Parameters:
        reservation: Reservation data from PIMS
        orderForms: PIMS order forms interface with additional booking details
    
    Returns:
        A Booking object with basic information filled in
    """
    booking = Booking()
    booking.guest.lastName = orderForms.lastName
    booking.guest.firstName = None
    booking.details.enquirySource = 'PIMS'
    booking.details.PIMSId = reservation['orderId']
    booking.property.shortName = orderForms.propertyName
    booking.arrival.date = reservation['arrival']
    booking.details.platformId = None
    booking.details.id = None
    return booking


def get_name_for_PIMS(booking: Booking) -> str:
    """
    Generate the standardized guest name for PIMS.
    
    Parameters:
        booking: Booking object with guest and platform information
    
    Returns:
        Formatted name string with platform source and guest name
    """
    source = booking.details.enquirySource
    return f'{source} - {booking.guest.lastName}'


def guest_name_is_generic(guest: str) -> bool:
    """
    Check if a guest name is a generic placeholder.
    
    Identifies names that are likely auto-generated by platforms or
    temporary placeholders.
    
    Parameters:
        guest: Guest name to check
    
    Returns:
        True if the name appears to be a generic placeholder
    """
    #if re.search(r'- [0-9]+$', guest.strip()): 
    #    return True
    if 'closed' in guest.lower(): 
        return True
    if 'reserved' in guest.lower(): 
        return True
    if 'tentative' in guest.lower(): 
        return True
    return False


# Database query functions
def get_PIMS_booking(database: Database, pimsId: str | int) -> Booking | None:
    """
    Get a booking from the database by PIMS ID.
    
    Parameters:
        database: Database connection
        pimsId: PIMS booking ID to search for
    
    Returns:
        Booking object if found, None otherwise
    """
    search = get_booking(database, PIMSId=pimsId)
    get_database_details(search)
    return search.fetchone()


def get_no_platId_booking(database: Database, start: date, end: date, 
                         propertyName: str) -> Booking | None:
    """
    Find a booking without a platform ID based on dates and property.
    
    Parameters:
        database: Database connection
        start: Booking arrival date
        end: Booking departure date
        propertyName: Property name or ID
    
    Returns:
        Booking object if found, None otherwise
    """
    search = search_valid_bookings(database, propertyName=propertyName)
    get_database_details(search)

    where = search.arrivals.where()
    where.date().isEqualTo(start)

    where = search.departures.where()
    where.date().isEqualTo(end)

    where = search.details.where()
    where.PIMSId().isNullEmptyOrFalse()

    return search.fetchone()


def get_database_details(search: Database) -> Database:
    """
    Configure search to retrieve necessary booking details.
    
    Parameters:
        search: Database search object
    
    Returns:
        Configured search object
    """
    select = search.details.select()    
    select.PIMSId()
    select.enquirySource()
    select.isOwner()
    select.adults()
    select.children()
    select.babies()
    select.platformId()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()

    select = search.properties.select()
    select.shortName()

    select = search.charges.select()
    select.basicRental()
    select.currency()
    
    select = search.guests.select()
    select.lastName()
    select.firstName()

    return search


def is_platform_owner_booking(booking: Booking) -> None:
    """
    Determine if a booking is an owner booking based on enquiry source and property.
    
    Parameters:
        booking: Booking object to evaluate
    Returns:
        bool indicating if the booking is an owner booking
    """
    return booking.details.enquirySource == 'Booking.com' and booking.property.shortName == 'A24'