from default.booking.booking import Booking
from default.database.functions import search_valid_bookings, search_properties
from default.database.database import Database
import datetime
from typing import List, Optional
from default.property.property import Property


def get_tourist_tax_properties(propertyId: Optional[int] = None, propertyName: Optional[str] = None) -> List[Property]:
    """
    Retrieve properties from the database for TMT registration.
    
    Queries the database for properties that meet TMT registration criteria,
    including those that are bookable through the system and have valid
    AL (Alojamento Local) numbers.
    
    Args:
        propertyId (Optional[int]): Specific property ID to retrieve (default: None)
        propertyName (Optional[str]): Property name pattern for LIKE search (default: None)
        
    Returns:
        List[Property]: List of Property objects matching the criteria
        
    Query Criteria:
        - Must have weBook = True (bookable properties)
        - Must have valid AL number (required for TMT registration)
        - Optionally filtered by ID or name pattern
    """
    # Initialize database search for properties
    search = search_properties()

    # Select required property fields
    select = search.properties.select()
    select.alNumber()  # AL number required for TMT registration

    # Select required property fields
    select = search.propertySpecs.select()
    select.bedrooms()
    select.maxGuests()

    # Select address information needed for registration
    select = search.propertyAddresses.select()
    select.street()  # Street address required

    # Apply property ID filter if specified
    if propertyId:
        where = search.properties.where()
        where.id().isEqualTo(propertyId)

    # Apply property name filter if specified (case-insensitive partial match)
    if propertyName:
        where = search.properties.where()
        where.name().isLike(f'%{propertyName}%')

    # Filter to only bookable properties (required for TMT)
    where = search.properties.where()
    where.weBook().isTrue()
  
    # Execute query and return results
    result = search.fetchall()    
    search.close()  # Ensure database connection is closed
    return result


def calculate_tourist_tax(bookings: list[Booking]) -> float:
    """
    Calculate the tourist tax for a given property based on its specifications.
    This is a placeholder function and should be implemented with the actual tax calculation logic.
    """
    # Example calculation (this should be replaced with the actual logic):
    total = 0
    for booking in bookings:
        # Assuming a flat rate of 1.5 per guest per night for demonstration
        nights = booking.totalNights
        adults = booking.details.adults
        if nights > 7:
            nights = 7  # Cap at 7 nights for tax calculation
        total += adults * nights
    return total


def get_tourist_tax_bookings(database: Database, start: datetime.date, end: datetime.date, propertyName: str) -> list[Booking]:
    """
    Retrieve bookings from the database that are relevant for tourist tax calculation.
    This function queries the database for bookings that fall within the specified date 
    range and match the given property name. It filters out bookings that are not relevant 
    for tourist tax purposes, such as those made directly or through Booking.com, and ensures 
    that only bookings with a valid owner are included.
    
    Args:
        database (Database): The database instance to query
        start (datetime.date): The start date for the booking search
        end (datetime.date): The end date for the booking search
        propertyName (str): The name of the property to filter bookings by (used in a LIKE search)
        
    Returns:
        list[Booking]: List of bookings matching the criteria
    """
    search = search_valid_bookings(database, start=start, end=end, propertyName=propertyName)

    select = search.details.select()
    select.adults()
    select.enquirySource()

    select = search.arrivals.select()
    select.date()

    select = search.departures.select()
    select.date()

    where = search.details.where()
    where.isOwner().isFalse()
    where.enquirySource().isNotIn(('Direct', 'Booking.com'))

    return search.fetchall()