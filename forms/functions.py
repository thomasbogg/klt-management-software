from datetime import date

from default.database.database import Database
from default.database.functions import (
    search_bookings,
    set_valid_management_booking
)


def get_forms_bookings(database: Database, start: date, end: date, bookingId: int | None = None) -> Database:
    """
    Gets bookings with form data for a given date range or specific booking ID.
    
    Args:
        database: Database instance
        start: Start date
        end: End date
        bookingId: Optional specific booking ID
        
    Returns:
        Database search object with selections and conditions set
    """
    search = search_bookings(database, start, end)
    
    # Basic booking information
    select = search.details.select()
    select.enquiryDate()
    select.isOwner()
    
    # Arrival and departure information
    select = search.arrivals.select()
    select.id()
    select.date()
    
    select = search.departures.select()
    select.id()
    select.date()
    
    # Guest information
    select = search.guests.select()
    select.id()
    select.email()
    select.phone()
    select.firstName()
    select.lastName()
    select.preferredLanguage()
    
    # Related table IDs
    select = search.arrivals.select()
    select.id()

    select = search.departures.select()
    select.id()
    
    select = search.extras.select()
    select.id()
    
    # Property information
    select = search.properties.select()
    select.name()
    select.shortName()
    
    # Address information
    select = search.propertyAddresses.select()
    select.location()
    
    # Apply booking ID filter if specified
    if bookingId:
        where = search.details.where()
        where.id().isEqualTo(bookingId)

    # Set conditions for valid bookings
    set_valid_management_booking(search)
    
    return search