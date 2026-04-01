from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database, search_properties
from default.google.mail.functions import get_inbox
from default.update.wrapper import update
from platforms.airbnb.browser import BrowseAirbnb
from platforms.airbnb.reader import ReadAirbnbEmails
from platforms.functions import (
    update_booking_in_database, 
    update_PIMS_platform_bookings
)
from utils import string_to_float, toList


#######################################################
# MAIN UPDATE FUNCTION
#######################################################

@update
def update_from_airbnb(id: int | str | list[str] | None = None, 
                      start: date | None = None, 
                      end: date | None = None) -> str:
    """
    Update bookings from Airbnb, either from emails or based on provided parameters.
    
    Args:
        id: Optional booking ID(s) to update.
        start: Optional start date for range of bookings to update.
        end: Optional end date for range of bookings to update.
        
    Returns:
        A status message indicating the result of the operation.
    """
    if not id and not start and not end:
        messages = get_inbox(sender='automated@airbnb.com', subject='Reservation')
        if not messages: 
            return 'Not updating today!'
            
    browser = BrowseAirbnb().goTo().login()
    #browser = None # --- IGNORE ---
    database = get_database()
    
    if id or start or end:
        done = update_from_arguments(browser, database, id, start, end)
    else:
        done = update_from_emails(browser, database, messages)
        
    browser.quit()
    database.close()
    return done


#######################################################
# UPDATE SOURCE FUNCTIONS
#######################################################

def update_from_arguments(browser: BrowseAirbnb, database: Database, 
                         id: int | str | list[str] | None, 
                         start: date | None, 
                         end: date | None) -> str:
    """
    Update bookings from Airbnb based on specific arguments like ID or date range.
    
    Args:
        browser: BrowseAirbnb instance for web interaction.
        database: Database connection.
        id: Booking ID(s) to update.
        start: Start date for range of bookings to update.
        end: End date for range of bookings to update.
        
    Returns:
        A status message indicating the result of the operation.
    """
    id = toList(id)
    valid = browser.validReservations(ids=id, start=start, end=end).list
    lenValid = len(valid)
    update_bookings_from_airbnb(database, valid)
    
    if id and len(id) == lenValid:
        return f'Successfully updated Reservation(s) {id}'
        
    completed = browser.completedReservations(ids=id, start=start, end=end).list
    lenCompleted = len(completed)
    update_bookings_from_airbnb(database, completed)
    
    if id and len(id) == lenCompleted + lenValid:
        return f'Successfully updated Reservation(s) {id}'
        
    cancelled = browser.cancelledReservations(ids=id, start=start, end=end).list
    update_bookings_from_airbnb(database, cancelled)
    
    if id:
        return f'Successfully updated Reservation(s) {id}'
        
    return f'Successfully updated reservations from {start} to {end}'


def update_from_emails(browser: BrowseAirbnb, database: Database, 
                      messages: list) -> str:
    """
    Update bookings from Airbnb based on received email notifications.
    
    Args:
        browser: BrowseAirbnb instance for web interaction.
        database: Database connection.
        messages: List of email messages to process.
        
    Returns:
        A status message indicating the result of the operation.
    """
    reader = ReadAirbnbEmails(messages)
    new = reader.newBookings
    updated = reader.updatedBookings
    cancelled = reader.cancelledBookings
    
    if new or updated:
        valid = browser.validReservations(ids=(list(new.keys()) + updated)).list
        update_bookings_from_airbnb(database, valid, new)
        
    if cancelled:
        cancelled = browser.cancelledReservations(ids=cancelled).list
        update_bookings_from_airbnb(database, cancelled)
        
    if updated: 
        update_PIMS_platform_bookings(database, updated)
        
    reader.deleteRead()
    return 'Successfully updated reservations from emails!'


#######################################################
# DATABASE PROCESSING FUNCTIONS
#######################################################

def update_bookings_from_airbnb(database: Database, 
                               reservations: list[dict[str, str]], 
                               new: dict[str, str] | None = None) -> None:
    """
    Recursively process a list of reservations and update the database.
    
    Args:
        database: Database connection.
        reservations: List of reservation dictionaries from Airbnb.
        new: Dictionary of new bookings with their host service fees.
        
    Returns:
        None
    """
    if not reservations:
        return None
        
    reservation = reservations.pop()
    booking = set_booking_object(database, reservation, new)
    
    if booking:
        update_booking_in_database(database, booking)
        
    return update_bookings_from_airbnb(database, reservations, new)


def set_booking_object(database: Database, reservation: dict[str, str], new: dict[str, str] | None = None) -> Booking:
    """
    Create a booking object from an Airbnb reservation.
    
    Args:
        database: Database connection.
        reservation: Dictionary containing reservation details.
        new: Dictionary of new bookings with their host service fees.
        
    Returns:
        A populated Booking object.
    """
    booking = Booking(database)
    details = booking.details
    details.propertyId = get_airbnb_property_id(reservation['propertyName'])
    details.platformId = reservation['platformId']
    details.enquiryStatus = reservation['enquiryStatus']
    
    if details.enquiryStatus == 'Booking cancelled':
        return booking
        
    details.enquirySource = 'Airbnb'
    details.adults, details.children, details.babies = sort_guests(reservation['guests'])
    details.enquiryDate = reservation['enquiryDate']
    
    booking.charges.currency = 'EUR'    
    booking.charges.basicRental = string_to_float(reservation['payoutTotal'])
    #booking.charges.platformFee = string_to_float(reservation['platformFee'])
    booking.charges.admin = 0
    
    names = reservation['guestNames'].split()
    booking.guest.firstName = names[0].title() if len(names) == 1 else ' '.join(names[:-1]).title()
    booking.guest.lastName = '' if len(names) == 1 else names[-1].title()
    booking.guest.phone = reservation['guestPhone']
    
    booking.arrival.date = reservation['arrivalDate']
    booking.departure.date = reservation['departureDate']

    if new and details.platformId in new.keys():
        booking.charges.platformFee = string_to_float(new[details.platformId])

    return booking


#######################################################
# HELPER FUNCTIONS
#######################################################

def sort_guests(string: str) -> tuple[int, int, int]:
    """
    Parse guest count information from an Airbnb guest string.
    
    Args:
        string: The string containing guest count information (e.g., "2 adults, 1 child").
        
    Returns:
        A tuple of (adults, children, babies) counts.
    """
    adults, children, babies = 0, 0, 0
    
    for guest in string.split(','):
        guest = guest.strip()
        
        if 'adult' in guest:
            adults += int(guest.split()[0])
        elif 'child' in guest:
            children += int(guest.split()[0])
        elif 'infant' in guest:
            babies += int(guest.split()[0])
            
    return adults, children, babies    


def get_airbnb_property_id(name: str) -> int:
    """
    Get the internal property ID that corresponds to an Airbnb property name.
    
    Args:
        name: The Airbnb property name to search for.
        
    Returns:
        The internal property ID.
        
    Raises:
        ValueError: If property with the specified name is not found.
    """
    search = search_properties()
    search.properties.where().airbnbName().isEqualTo(name)
    result = search.fetchone()
    
    if result:
        return result.name
    else:
        raise ValueError(f'Property with name {name} not found.')