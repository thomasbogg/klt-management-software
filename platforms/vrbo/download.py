from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database,
    search_properties,
    search_valid_bookings
)
from default.dates import dates
from default.google.mail.functions import get_inbox
from default.property.property import Property
from default.update.wrapper import update
from platforms.functions import (
    update_booking_in_database, 
    update_PIMS_platform_bookings
)
from platforms.vrbo.browser import BrowseVrbo
from platforms.vrbo.reader import ReadVrboEmails
from utils import log, logerror


#######################################################
# MAIN UPDATE FUNCTION
#######################################################

@update
def update_from_vrbo(start: date | None = None, end: date | None = None) -> str:
    """
    Update bookings from VRBO platform.
    
    Retrieves booking data from email notifications and/or the VRBO website,
    updates the database, and syncs with PIMS for updated reservations.
    
    Parameters:
        start: Optional start date for retrieving reservations
        end: Optional end date for retrieving reservations
        
    Returns:
        Success message or notification that no update was needed
    """
    messages = list()
    bookings = list()
    database = get_database()
    
    if not start and not end:
        in28Days = dates.calculate(days=28)
        bookings = get_vrbo_bookings(database, date=in28Days)
        messages = get_inbox(sender='sender@messages.homeaway.com', subject='Booking')
        
        if not messages and not bookings:
            database.close()
            return 'Not updating today!'
        
    elif start and end and start == end:
        bookings = get_vrbo_bookings(database, date=start)
        start = end = None
    
    propIdsDates, reader = get_prop_ids_dates(messages)
    guestNamesDates = get_guest_names_dates(bookings)
    reservations = get_reservations(propIdsDates, guestNamesDates, start, end)    
    toUpdate = list()
    
    for reservation in reservations:
        booking = set_booking_object(database, reservation)
        if not booking:
            continue
        update_booking_in_database(database, booking)
        
        if 'isUpdated' in reservation:
            toUpdate.append(booking.details.platformId)

    if reader:
        reader.deleteRead()
        pass

    if toUpdate:
        update_PIMS_platform_bookings(database, toUpdate)

    database.close()
    return 'Successfully updated VRBO bookings!'


#######################################################
# DATA RETRIEVAL FUNCTIONS
#######################################################

def get_vrbo_bookings(database: Database, date: date | None = None) -> list[Booking]:
    """
    Get upcoming VRBO bookings from the database.
    
    Parameters:
        database: Database connection
        date: Optional date to filter bookings for
        
    Returns:
        List of Booking objects for VRBO bookings
    """
    search = search_valid_bookings(database)
    
    where = search.details.where()
    where.enquirySource().isEqualTo('Vrbo')
    
    if date:
        search.arrivals.where().date().isEqualTo(date)
    
    select = search.guests.select()
    select.lastName()
    
    select = search.arrivals.select()
    select.date()
    
    select = search.departures.select()
    select.date()
    
    return search.fetchall()


def get_prop_ids_dates(messages: list) -> tuple[dict, ReadVrboEmails | None]:
    """
    Extract property IDs and dates from email notifications.
    
    Parameters:
        messages: List of email messages to process
        
    Returns:
        Tuple containing:
          - Dictionary with property IDs mapped to dates
          - Email reader object or None if no messages provided
    """
    propIdsDates = {'total': 0}
    if not messages:
        return propIdsDates, None
    
    reader = ReadVrboEmails(messages)
    new = reader.newBookings
    updated = reader.updatedBookings
    cancelled = reader.cancelledBookings
 
    if new:
        propIdsDates['new'] = new
        propIdsDates['total'] += new['total']
 
    if updated:
        propIdsDates['updated'] = updated
        propIdsDates['total'] += updated['total']
 
    if cancelled:
        propIdsDates['cancelled'] = cancelled
        propIdsDates['total'] += cancelled['total']
 
    return propIdsDates, reader


def get_guest_names_dates(bookings: list[Booking]) -> dict:
    """
    Create mapping of guest names to their booking dates.
    
    Parameters:
        bookings: List of Booking objects to process
        
    Returns:
        Dictionary mapping guest last names to tuples of (arrival_date, departure_date)
    """
    guestNamesDates = {'total': 0}
    if not bookings:
        return guestNamesDates
    
    for booking in bookings:
        guestNamesDates['total'] += 1
        guestNamesDates[booking.guest.lastName] = (booking.arrival.date, booking.departure.date)
    return guestNamesDates


def get_reservations(
    propIdsDates: dict, 
    guestNamesDates: dict, 
    start: date | None = None, 
    end: date | None = None
) -> list[dict]:
    """
    Get reservations from VRBO website using filters.
   
    Parameters:
        propIdsDates: Dictionary mapping property IDs to dates
        guestNamesDates: Dictionary mapping guest names to dates
        start: Optional start date for filtering reservations
        end: Optional end date for filtering reservations
    
    Returns:
        List of reservation dictionaries with booking details
    
    Raises:
        Exception: If unable to retrieve reservations from VRBO website after 3 attempts
    """
    total = propIdsDates['total'] + guestNamesDates['total']
    tries = 0
    while tries < 3:
        tries += 1
        browser = BrowseVrbo().goTo().login()
        #input('Press Enter to continue...')
        reservations = browser.reservations(propIdsDates, guestNamesDates, start, end).list
        browser.quit()
        if reservations:
            if total > 0 and len(reservations) < total:
                continue
            return reservations
       
        log('Trying again to get reservations from Vrbo website')
    
    raise Exception(
        'FATAL: Could not retrieve reservations from Vrbo website')


#######################################################
# BOOKING OBJECT CREATION
#######################################################

def set_booking_object(database: Database, reservation: dict) -> Booking:
    """
    Create a booking object from reservation data.
    
    Parameters:
        database: Database connection
        reservation: Dictionary containing reservation details
        
    Returns:
        Populated Booking object ready for database insertion or update
    """
    booking = Booking(database)

    # Set booking details
    booking.details.platformId = reservation['platformId']
    booking.details.enquiryStatus = reservation['enquiryStatus']

    if not booking.statusIsOkay:
        return booking
    
    booking.details.enquirySource = 'Vrbo'
    booking.details.propertyId = get_property_id_from_vrbo_id(reservation['propertyId'])
    booking.details.enquiryDate = reservation['enquiryDate']
    booking.details.adults = reservation['guests']['adults']
    booking.details.children = reservation['guests']['children']
    booking.details.babies = reservation['guests']['babies']
   
    # Set guest details
    booking.guest.firstName = reservation['guestFirstName'].title()
    booking.guest.lastName = reservation['guestLastName'].title()
    booking.guest.phone = reservation['guestPhone']
    booking.guest.email = reservation['guestEmail']

    # Set dates
    booking.arrival.date = reservation['arrivalDate']
    booking.departure.date = reservation['departureDate']    
    
    # Set charges
    booking.charges.currency = 'EUR'
    booking.charges.basicRental = reservation['payoutTotal']
    booking.charges.platformFee = reservation['platformFee']
    booking.charges.admin = 0

    return booking


def get_property_id_from_vrbo_id(vrboPropertyId: str) -> Property | None:
    """
    Retrieve the VRBO property ID from the database based on the property name.
    
    Parameters:
        database: Database connection
        vrboPropertyId: Vrbo Id of the property to search for
        
    Returns:
        VRBO property ID if found, None otherwise
    """
    search = search_properties()

    where = search.properties.where()
    where.vrboId().isEqualTo(vrboPropertyId)

    id = search.fetchone().id
    search.close()
    return id