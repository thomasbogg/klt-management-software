from correspondence.functions import get_email_bookings
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database


#######################################################
# DATABASE QUERY FUNCTIONS
#######################################################

def get_management_email_bookings(
        database: Database, 
        start: date = None, 
        end: date = None, 
        emailSent: bool = False, 
        bookingId: int = None):
    """
    Retrieves management email bookings with specified conditions.

    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        emailSent: Whether management email has been sent
        bookingId: The specific booking ID to filter by

    Returns:
        A search object with the selected data and applied conditions
    """
    # Initialize search using the higher-level function
    search = get_email_bookings(database, bookingId, noBlocks=True)
    
    # Select details from the bookings table
    select = search.details.select()
    select.enquiryStatus()
    select.adults()
    select.children()
    select.babies()
    select.isOwner()
    
    # Select arrival details
    search.arrivals.select().all()
    
    # Select departure details
    search.departures.select().all()
    
    # Select property owner details (excluding default_clean and default_owner_meet_greet)
    select = search.propertyOwners.select()
    select.name()
    
    # Select all extras
    search.extras.select().all()
    
    # Apply date range conditions if provided
    if start and end:
        where = search.arrivals.where()
        where.date().isGreaterThanOrEqualTo(start)
        where.date().isLessThanOrEqualTo(end)
    
    # Apply email conditions if not filtering by bookingId
    if not bookingId:
        whereEmails = search.emails.where()
        whereEmails.management().isEqualTo(emailSent)
    
    # Set order by arrival date
    search.arrivals.order().date()
    
    return search


#######################################################
# PROPERTY MANAGER FUNCTIONS
#######################################################

def determine_manager_name(booking: Booking) -> str:
    """
    Determine the name of the property manager based on booking details.
    
    Args:
        booking: The booking containing property information
        
    Returns:
        Manager name for email correspondence
    """
    if booking.property.weClean:
        return 'Mum'
    return booking.property.manager.name


def determine_manager_email(booking: Booking) -> str:
    """
    Determine the email address of the property manager based on booking details.
    
    Args:
        booking: The booking containing property information
        
    Returns:
        Manager email address for correspondence
    """
    if booking.property.weClean:
        return booking.property.manager.cleaningEmail
    return booking.property.manager.email


#######################################################
# FLIGHT INFORMATION FUNCTIONS
#######################################################

def determine_lack_of_inbound_flight_information(booking: Booking) -> bool:
    """
    Check if inbound flight information is missing.
    
    Args:
        booking: The booking containing arrival details
        
    Returns:
        True if inbound flight information is missing, False otherwise
    """
    return not booking.arrival.flightNumber or not booking.arrival.time


def determine_lack_of_outbound_flight_information(booking: Booking) -> bool:
    """
    Check if outbound flight information is missing.
    
    Args:
        booking: The booking containing departure details
        
    Returns:
        True if outbound flight information is missing, False otherwise
    """
    return not booking.departure.flightNumber or not booking.departure.time


#######################################################
# UPDATE NOTIFICATION FUNCTIONS
#######################################################

def should_advise_transfers(booking: Booking, update: str) -> bool:
    """
    Determine if airport transfer service should be notified about booking changes.
    
    Args:
        booking: The booking containing extras information
        update: Description of the update/change
        
    Returns:
        True if transfer service should be notified, False otherwise
    """
    update = update.lower()
    
    if 'child seats' in update:
        return True
    
    if 'excess baggage' in update:
        return True
        
    if 'number of guests' in update:
        return True
    
    if 'arrival' in update:
        if booking.extras.airportTransfers:
            return True
        if booking.extras.airportTransferInboundOnly:
            return True
  
    elif 'departure' in update:
        if booking.extras.airportTransfers:
            return True
        if booking.extras.airportTransferOutboundOnly:
            return True
   
    return False
