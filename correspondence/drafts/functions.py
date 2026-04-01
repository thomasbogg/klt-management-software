from datetime import date

from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    search_properties,
    search_valid_bookings,
    set_property_location
)
from default.property.property import Property


def get_guest_email_addresses(
    start: date = None,
    end: date = None, 
    weBook: bool = None, 
    isBarracuda: bool = None, 
    isMonaco: bool = None, 
    isCorcovada: bool = None, 
    hasAl: bool = None,
    **kwargs
) -> list[Booking]:
    """
    Get guest email addresses for bookings within a date range with optional property filters.
    
    Retrieves booking records with guest contact information, filtered by date range
    and property characteristics.
    
    Args:
        start: Start date for departure
        end: End date for arrival
        weBook: Filter for properties we book
        isBarracuda: Filter for properties in Barracuda
        isMonaco: Filter for properties in Monaco
        isCorcovada: Filter for properties in Corcovada
        hasAl: Filter for properties with AL number
        
    Returns:
        List of Booking objects with guest email information
    """
    # Initialize search with valid bookings
    search: Database = search_valid_bookings(noBlocks=True)
    
    # Select necessary columns
    select = search.properties.select()
    select.shortName()
    
    select = search.guests.select()
    select.firstName()
    select.lastName()
    select.email()
    
    # Set property conditions
    set_property_location(
                        search,     
                        isBarracuda=isBarracuda, 
                        isMonaco=isMonaco, 
                        isCorcovada=isCorcovada
                    )
    where = search.properties.where()

    if hasAl is not None:
        where.alNumber().isNotNullEmptyOrFalse()

    if weBook is not None:
        where.weBook().isEqualTo(weBook)

    # Set date conditions
    if start is not None:
        search.departures.where().date().isGreaterThanOrEqualTo(start)
    if end is not None:
        search.arrivals.where().date().isLessThanOrEqualTo(end)
    
    # Return results
    return [booking.guest for booking in search.fetchall()]


def get_owner_email_addresses(
    weBook: bool = None, 
    isBarracuda: bool = None, 
    isMonaco: bool = None, 
    isCorcovada: bool = None, 
    hasAl: bool = None, 
    notShortNames: list[str] = None,
    **kwargs
) -> list[Property]:
    """
    Get property owner email addresses with optional property filters.
    
    Retrieves property records with owner contact information, filtered by
    property characteristics and location.
    
    Args:
        weBook: Filter for properties we book
        isBarracuda: Filter for properties in Barracuda
        isMonaco: Filter for properties in Monaco
        isCorcovada: Filter for properties in Corcovada
        hasAl: Filter for properties with AL number
        notShortNames: List of property short names to exclude
        
    Returns:
        List of Property objects with owner email information
    """
    # Initialize search with properties as primary table
    search: Database = search_properties()

    # Select necessary columns
    select = search.properties.select()
    select.shortName()
    
    select = search.propertyOwners.select()
    select.name()
    select.email()
    
    # Set property conditions
    set_property_location(
                        search,     
                        isBarracuda=isBarracuda, 
                        isMonaco=isMonaco, 
                        isCorcovada=isCorcovada
                    )
    where = search.properties.where()
    
    if weBook is not None:
        where.weBook().isEqualTo(weBook)
    
    # Certify that the property is valid
    if not weBook:
        where.weClean().isTrue()
    
    if hasAl is not None:
        where.alNumber().isNotNullEmptyOrFalse()
    
    if notShortNames:
        print(f'Excluding properties: {notShortNames}')  # Debugging line
        where.shortName().isNotIn(tuple(notShortNames))
    
    # Return results
    return  [property.owner for property in search.fetchall()]